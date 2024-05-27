import re
import sys

input_file_name = '1_provider_dnum.sql'
output_file_name = '1_provider_out.sql'

if (len(sys.argv) < 2):
    dejima_table_name = "dnum"
else:
    dejima_table_name = sys.argv[1]


def my_insert(str, str_inserted, start_split_index, end_split_index=-1):
    if end_split_index == -1:
        end_split_index = start_split_index
    return str[:start_split_index] + str_inserted + str[end_split_index:]
    

with open(input_file_name) as f:
    str = f.read()



# ---------- add a new function to be called by python ----------
split_index = re.search('CREATE EXTENSION IF NOT EXISTS plsh;', str).end()+1
str_inserted = """
CREATE TABLE IF NOT EXISTS public.__dummy__dnum_detected_deletions (txid int, LIKE public.dnum );
CREATE INDEX IF NOT EXISTS idx__dummy__dnum_detected_deletions ON public.__dummy__dnum_detected_deletions (txid);
CREATE TABLE IF NOT EXISTS public.__dummy__dnum_detected_insertions (txid int, LIKE public.dnum );
CREATE INDEX IF NOT EXISTS idx__dummy__dnum_detected_insertions ON public.__dummy__dnum_detected_insertions (txid);

CREATE OR REPLACE FUNCTION public.dnum_get_detected_update_data(txid int)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  deletion_data text;
  insertion_data text;
  json_data text;
  BEGIN
    insertion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__dnum_detected_insertions as t where t.txid = $1);
    IF insertion_data IS NOT DISTINCT FROM NULL THEN 
        insertion_data := '[]';
    END IF; 
    deletion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__dnum_detected_deletions as t where t.txid = $1);
    IF deletion_data IS NOT DISTINCT FROM NULL THEN 
        deletion_data := '[]';
    END IF; 
    IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN 
        json_data := concat('{"view": ' , '"public.dnum"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
    END IF;
    RETURN json_data;
  END;
$$;
"""
str = my_insert(str, str_inserted, split_index)



# ---------- detect update on dejima table ----------
start_split_index = re.search('CREATE OR REPLACE FUNCTION public.dnum_detect_update()', str).start()
end_split_index = start_split_index + re.search('RETURN NULL;', str[start_split_index:]).end()

detect_update = str[start_split_index:end_split_index]

detect_update = my_insert(detect_update, "  xid int;\n", re.search("user_name text;", detect_update).end()+1)
detect_update = detect_update.replace('\n    ', '\n        ')
detect_update = my_insert(detect_update, "  END IF;\n  ", list(re.finditer('END IF', detect_update))[-1].span()[0])

old_str = """
  IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'dnum_delta_action_flag') THEN"""
new_str = """
  IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'bt_detect_update_on_dnum_flag') THEN
    CREATE TEMPORARY TABLE bt_detect_update_on_dnum_flag ON COMMIT DROP AS (SELECT true as finish);
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'dnum_delta_action_flag') THEN"""
detect_update = detect_update.replace(old_str, new_str)

old_str = """
            IF NOT (user_name = 'dejima') THEN 
                json_data := concat('{"view": ' , '"public.dnum"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');"""
new_str = """
            IF NOT (user_name = 'dejima') THEN 
                xid := (SELECT txid_current());
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.dnum"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');"""
detect_update = detect_update.replace(old_str, new_str)

old_str = """
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;"""
new_str = """
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;
                xid := (SELECT txid_current());

                -- update the table that stores the insertions and deletions we calculated
                INSERT INTO public.__dummy__dnum_detected_deletions
                    ( SELECT xid, * FROM (SELECT * FROM public.__dummy__materialized_dnum EXCEPT SELECT * FROM public.dnum) as detected_deletions_alias );

                INSERT INTO public.__dummy__dnum_detected_insertions
                    ( SELECT xid, * FROM (SELECT * FROM public.dnum EXCEPT SELECT * FROM public.__dummy__materialized_dnum) as detected_insertions_alias );
                    
                REFRESH MATERIALIZED VIEW public.__dummy__materialized_dnum;"""
detect_update = detect_update.replace(old_str, new_str)

str = my_insert(str, detect_update, start_split_index, end_split_index)



# ---------- non trigger detect update on dejima table ----------
start_split_index = re.search('CREATE OR REPLACE FUNCTION public.non_trigger_dnum_detect_update()', str).start()
end_split_index = start_split_index + re.search('\$\$;\n\n', str[start_split_index:]).end()
str = my_insert(str, "", start_split_index, end_split_index)



# ---------- add a new function to be called by python ----------
old_str = """
DROP TRIGGER IF EXISTS bt_detect_update_dnum ON public.bt;
        CREATE TRIGGER bt_detect_update_dnum
            AFTER INSERT OR UPDATE OR DELETE ON
            public.bt FOR EACH STATEMENT EXECUTE PROCEDURE public.dnum_detect_update();"""
new_str = """
DROP TRIGGER IF EXISTS bt_trigger_detect_update_on_dnum ON public.bt;
CREATE CONSTRAINT TRIGGER bt_trigger_detect_update_on_dnum
    AFTER INSERT OR UPDATE OR DELETE ON
    public.bt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE public.bt_detect_update_on_dnum();

CREATE OR REPLACE FUNCTION public.bt_propagate_updates_to_dnum ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS public.bt_trigger_detect_update_on_dnum IMMEDIATE;
    SET CONSTRAINTS public.bt_trigger_detect_update_on_dnum DEFERRED;
    DROP TABLE IF EXISTS bt_detect_update_on_dnum_flag;
    RETURN true;
  END;
$$;"""
str = str.replace(old_str, new_str)



# ---------- delta action on dejima table ----------
start_split_index = re.search('CREATE OR REPLACE FUNCTION public.dnum_delta_action()', str).start()
end_split_index = start_split_index + re.search('\$\$;', str[start_split_index:]).end()

detect_update = str[start_split_index:end_split_index]

detect_update = my_insert(detect_update, "  xid int;\n", re.search("user_name text;", detect_update).end()+1)


old_str = """
            IF NOT (user_name = 'dejima') THEN 
                json_data := concat('{"view": ' , '"public.dnum"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');"""
new_str = """
            IF NOT (user_name = 'dejima') THEN 
                xid := (SELECT txid_current());
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.dnum"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');"""
detect_update = detect_update.replace(old_str, new_str)

old_str = """
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;"""
new_str = """
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;
                xid := (SELECT txid_current());
                
                -- update the table that stores the insertions and deletions we calculated
                INSERT INTO public.__dummy__dnum_detected_deletions
                    ( SELECT xid, * FROM (SELECT * FROM __temp__Δ_del_dnum INTERSECT SELECT * FROM public.__dummy__materialized_dnum) as detected_deletions_alias );

                INSERT INTO public.__dummy__dnum_detected_insertions
                    ( SELECT xid, * FROM (SELECT * FROM __temp__Δ_ins_dnum EXCEPT SELECT * FROM public.__dummy__materialized_dnum) as detected_insertions_alias );
                    
                REFRESH MATERIALIZED VIEW public.__dummy__materialized_dnum;"""
detect_update = detect_update.replace(old_str, new_str)

str = my_insert(str, detect_update, start_split_index, end_split_index)



# ---------- materialization on dejima table ----------
start_split_index = re.search('CREATE OR REPLACE FUNCTION public.dnum_materialization()', str).start()
end_split_index = start_split_index + re.search('\$\$;', str[start_split_index:]).end()

materialization = str[start_split_index:end_split_index]

old_str = """
        CREATE TEMPORARY TABLE __temp__Δ_ins_dnum ( LIKE public.dnum INCLUDING ALL ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __temp__dnum_trigger_delta_action"""
new_str = """
        CREATE TEMPORARY TABLE __temp__Δ_ins_dnum ( LIKE public.dnum INCLUDING ALL ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __temp__dnum_trigger_delta_action_ins"""
materialization = materialization.replace(old_str, new_str)

old_str = """
        CREATE TEMPORARY TABLE __temp__Δ_del_dnum ( LIKE public.dnum INCLUDING ALL ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __temp__dnum_trigger_delta_action"""
new_str = """
        CREATE TEMPORARY TABLE __temp__Δ_del_dnum ( LIKE public.dnum INCLUDING ALL ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __temp__dnum_trigger_delta_action_del"""
materialization = materialization.replace(old_str, new_str)

str = my_insert(str, materialization, start_split_index, end_split_index)



# ---------- add new functions to be called by python ----------
str_inserted = """
CREATE OR REPLACE FUNCTION public.dnum_propagate_updates ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS __temp__dnum_trigger_delta_action_ins, __temp__dnum_trigger_delta_action_del IMMEDIATE;
    SET CONSTRAINTS __temp__dnum_trigger_delta_action_ins, __temp__dnum_trigger_delta_action_del DEFERRED;
    DROP TABLE IF EXISTS dnum_delta_action_flag;
    DROP TABLE IF EXISTS __temp__Δ_ins_dnum;
    DROP TABLE IF EXISTS __temp__Δ_del_dnum;
    RETURN true;
  END;
$$;

CREATE OR REPLACE FUNCTION public.clean_dummy_dnum ()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  xid int;
  BEGIN
    xid := (SELECT txid_current());
    DELETE FROM public.__dummy__dnum_detected_deletions as t where t.txid = xid;
    DELETE FROM public.__dummy__dnum_detected_insertions as t where t.txid = xid;
    RAISE LOG 'clean __dummy__dnum_detected_deletions/insertions';
    RETURN NULL;
  END;
$$;

CREATE CONSTRAINT TRIGGER __zzz_clean_dnum
    AFTER INSERT OR UPDATE OR DELETE ON
    public.bt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE public.clean_dummy_dnum();"""
str = str[:-1] + str_inserted


# ---------- replace throughout the whole ----------
str = str.replace("dnum_detect_update", "bt_detect_update_on_dnum")
str = str.replace("dnum", dejima_table_name)



with open(output_file_name, mode='w') as f:
    f.write(str)