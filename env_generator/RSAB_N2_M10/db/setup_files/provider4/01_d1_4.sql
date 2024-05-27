CREATE OR REPLACE VIEW public.d1_4 AS 
SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT d1_4_a5_0.COL0 AS COL0, d1_4_a5_0.COL1 AS COL1, d1_4_a5_0.COL2 AS COL2, d1_4_a5_0.COL3 AS COL3, d1_4_a5_0.COL4 AS COL4 FROM (SELECT bt_a7_0.V AS COL0, bt_a7_0.L AS COL1, bt_a7_0.D AS COL2, bt_a7_0.R AS COL3, bt_a7_0.LINEAGE AS COL4 FROM public.bt AS bt_a7_0 WHERE bt_a7_0.AL1 = 'true'  ) AS d1_4_a5_0   ) AS __dummy__   ;

CREATE EXTENSION IF NOT EXISTS plsh;

CREATE TABLE IF NOT EXISTS public.__dummy__d1_4_detected_deletions (txid int, LIKE public.d1_4 );
CREATE INDEX IF NOT EXISTS idx__dummy__d1_4_detected_deletions ON public.__dummy__d1_4_detected_deletions (txid);
CREATE TABLE IF NOT EXISTS public.__dummy__d1_4_detected_insertions (txid int, LIKE public.d1_4 );
CREATE INDEX IF NOT EXISTS idx__dummy__d1_4_detected_insertions ON public.__dummy__d1_4_detected_insertions (txid);

CREATE OR REPLACE FUNCTION public.d1_4_get_detected_update_data(txid int)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  deletion_data text;
  insertion_data text;
  json_data text;
  BEGIN
    insertion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__d1_4_detected_insertions as t where t.txid = $1);
    IF insertion_data IS NOT DISTINCT FROM NULL THEN
        insertion_data := '[]';
    END IF;
    deletion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__d1_4_detected_deletions as t where t.txid = $1);
    IF deletion_data IS NOT DISTINCT FROM NULL THEN
        deletion_data := '[]';
    END IF;
    IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN
        -- calcuate the update data
        json_data := concat('{"view": ' , '"public.d1_4"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
        -- clear the update data
        DELETE FROM public.__dummy__d1_4_detected_deletions t where t.txid = $1;
        DELETE FROM public.__dummy__d1_4_detected_insertions t where t.txid = $1;
    END IF;
    RETURN json_data;
  END;
$$;

CREATE OR REPLACE FUNCTION public.d1_4_run_shell(text) RETURNS text AS $$
#!/bin/sh

result=$(curl -s -X POST -H "Content-Type: application/json" $DEJIMA_EXECUTION_ENDPOINT -d "$1")
if  [ "$result" = "true" ];  then
    echo "true"
else 
    echo $result
fi
$$ LANGUAGE plsh;

CREATE OR REPLACE FUNCTION public.bt_materialization_for_d1_4()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
text_var1 text;
text_var2 text;
text_var3 text;
BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__tmp_delta_ins_bt_for_d1_4' OR table_name = '__tmp_delta_del_bt_for_d1_4')
    THEN
        -- RAISE LOG 'execute procedure bt_materialization_for_d1_4';
        CREATE TEMPORARY TABLE __tmp_delta_ins_bt_for_d1_4 ( LIKE public.bt ) WITH OIDS ON COMMIT DROP;
        CREATE TEMPORARY TABLE __tmp_delta_del_bt_for_d1_4 ( LIKE public.bt ) WITH OIDS ON COMMIT DROP;

    END IF;
    RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.bt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.bt ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS bt_trigger_materialization_for_d1_4 ON public.bt;
CREATE TRIGGER bt_trigger_materialization_for_d1_4
    BEFORE INSERT OR UPDATE OR DELETE ON
    public.bt FOR EACH STATEMENT EXECUTE PROCEDURE public.bt_materialization_for_d1_4();

CREATE OR REPLACE FUNCTION public.bt_update_for_d1_4()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
text_var1 text;
text_var2 text;
text_var3 text;
BEGIN
    -- RAISE LOG 'execute procedure bt_update_for_d1_4';
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'd1_4_delta_action_flag') THEN
        IF TG_OP = 'INSERT' THEN
        -- RAISE LOG 'NEW: %', NEW;
        IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
            RAISE check_violation USING MESSAGE = 'Invalid update: null value is not accepted';
        END IF;
        DELETE FROM __tmp_delta_del_bt_for_d1_4 WHERE ROW(V,L,D,R,AL2,AL1,LINEAGE)= NEW;
        INSERT INTO __tmp_delta_ins_bt_for_d1_4 SELECT (NEW).*;
        ELSIF TG_OP = 'UPDATE' THEN
        IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
            RAISE check_violation USING MESSAGE = 'Invalid update: null value is not accepted';
        END IF;
        DELETE FROM __tmp_delta_ins_bt_for_d1_4 WHERE ROW(V,L,D,R,AL2,AL1,LINEAGE) = OLD;
        INSERT INTO __tmp_delta_del_bt_for_d1_4 SELECT (OLD).*;
        DELETE FROM __tmp_delta_del_bt_for_d1_4 WHERE ROW(V,L,D,R,AL2,AL1,LINEAGE) = NEW;
        INSERT INTO __tmp_delta_ins_bt_for_d1_4 SELECT (NEW).*;
        ELSIF TG_OP = 'DELETE' THEN
        -- RAISE LOG 'OLD: %', OLD;
        DELETE FROM __tmp_delta_ins_bt_for_d1_4 WHERE ROW(V,L,D,R,AL2,AL1,LINEAGE) = OLD;
        INSERT INTO __tmp_delta_del_bt_for_d1_4 SELECT (OLD).*;
        END IF;
    END IF;
    RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.bt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.bt ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS bt_trigger_update_for_d1_4 ON public.bt;
CREATE TRIGGER bt_trigger_update_for_d1_4
    AFTER INSERT OR UPDATE OR DELETE ON
    public.bt FOR EACH ROW EXECUTE PROCEDURE public.bt_update_for_d1_4();

CREATE OR REPLACE FUNCTION public.bt_detect_update_on_d1_4()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
text_var1 text;
text_var2 text;
text_var3 text;
func text;
tv text;
deletion_data text;
insertion_data text;
json_data text;
result text;
user_name text;
xid int;
array_delta_del public.bt[];
array_delta_ins public.bt[];
detected_deletions public.d1_4[];
detected_insertions public.d1_4[];
delta_ins_size int;
delta_del_size int;
BEGIN
IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'bt_detect_update_on_d1_4_flag') THEN
    CREATE TEMPORARY TABLE bt_detect_update_on_d1_4_flag ON COMMIT DROP AS (SELECT true as finish);
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'd1_4_delta_action_flag') THEN
        SELECT array_agg(tbl) INTO array_delta_ins FROM __tmp_delta_ins_bt_for_d1_4 AS tbl;
        select count(*) INTO delta_ins_size FROM __tmp_delta_ins_bt_for_d1_4;
        SELECT array_agg(tbl) INTO array_delta_del FROM __tmp_delta_del_bt_for_d1_4 tbl;
        select count(*) INTO delta_del_size FROM __tmp_delta_del_bt_for_d1_4;

        WITH __tmp_delta_ins_bt_for_d1_4_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size),
        __tmp_delta_del_bt_for_d1_4_ar as (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size)
        SELECT array_agg(tbl) INTO detected_insertions FROM (SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT part_ins_d1_4_a5_0.COL0 AS COL0, part_ins_d1_4_a5_0.COL1 AS COL1, part_ins_d1_4_a5_0.COL2 AS COL2, part_ins_d1_4_a5_0.COL3 AS COL3, part_ins_d1_4_a5_0.COL4 AS COL4 FROM (SELECT p_0_a5_0.COL0 AS COL0, p_0_a5_0.COL1 AS COL1, p_0_a5_0.COL2 AS COL2, p_0_a5_0.COL3 AS COL3, p_0_a5_0.COL4 AS COL4 FROM (SELECT __tmp_delta_ins_bt_for_d1_4_ar_a7_0.V AS COL0, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.L AS COL1, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.D AS COL2, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.R AS COL3, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.LINEAGE AS COL4 FROM __tmp_delta_ins_bt_for_d1_4_ar AS __tmp_delta_ins_bt_for_d1_4_ar_a7_0 WHERE __tmp_delta_ins_bt_for_d1_4_ar_a7_0.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM (SELECT __tmp_delta_ins_bt_for_d1_4_ar_a7_1.D AS COL0, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.L AS COL1, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.LINEAGE AS COL2, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.R AS COL3, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.V AS COL4 FROM __tmp_delta_del_bt_for_d1_4_ar AS __tmp_delta_del_bt_for_d1_4_ar_a7_0, __tmp_delta_ins_bt_for_d1_4_ar AS __tmp_delta_ins_bt_for_d1_4_ar_a7_1 WHERE __tmp_delta_ins_bt_for_d1_4_ar_a7_1.L = __tmp_delta_del_bt_for_d1_4_ar_a7_0.L AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.R = __tmp_delta_del_bt_for_d1_4_ar_a7_0.R AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL2 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.AL2 AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.V = __tmp_delta_del_bt_for_d1_4_ar_a7_0.V AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.AL1 AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.D = __tmp_delta_del_bt_for_d1_4_ar_a7_0.D AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.LINEAGE = __tmp_delta_del_bt_for_d1_4_ar_a7_0.LINEAGE AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = 'true' AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = 'true'   UNION SELECT __tmp_delta_ins_bt_for_d1_4_ar_a7_1.D AS COL0, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.L AS COL1, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.LINEAGE AS COL2, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.R AS COL3, __tmp_delta_ins_bt_for_d1_4_ar_a7_1.V AS COL4 FROM public.bt AS bt_a7_0, __tmp_delta_ins_bt_for_d1_4_ar AS __tmp_delta_ins_bt_for_d1_4_ar_a7_1 WHERE __tmp_delta_ins_bt_for_d1_4_ar_a7_1.L = bt_a7_0.L AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.R = bt_a7_0.R AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL2 = bt_a7_0.AL2 AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.V = bt_a7_0.V AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = bt_a7_0.AL1 AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.D = bt_a7_0.D AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.LINEAGE = bt_a7_0.LINEAGE AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = 'true' AND __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM (SELECT __tmp_delta_ins_bt_for_d1_4_ar_a7_0.AL1 AS COL0, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.D AS COL1, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.AL2 AS COL2, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.L AS COL3, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.LINEAGE AS COL4, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.R AS COL5, __tmp_delta_ins_bt_for_d1_4_ar_a7_0.V AS COL6 FROM __tmp_delta_ins_bt_for_d1_4_ar AS __tmp_delta_ins_bt_for_d1_4_ar_a7_0 WHERE __tmp_delta_ins_bt_for_d1_4_ar_a7_0.AL1 = 'true'  ) AS p_2_a7 WHERE p_2_a7.COL6 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.V AND p_2_a7.COL5 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.R AND p_2_a7.COL4 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.LINEAGE AND p_2_a7.COL3 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.L AND p_2_a7.COL2 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL2 AND p_2_a7.COL1 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.D AND p_2_a7.COL0 = __tmp_delta_ins_bt_for_d1_4_ar_a7_1.AL1 )  ) AS p_1_a5 WHERE p_1_a5.COL4 = __tmp_delta_ins_bt_for_d1_4_ar_a7_0.V AND p_1_a5.COL3 = __tmp_delta_ins_bt_for_d1_4_ar_a7_0.R AND p_1_a5.COL2 = __tmp_delta_ins_bt_for_d1_4_ar_a7_0.LINEAGE AND p_1_a5.COL1 = __tmp_delta_ins_bt_for_d1_4_ar_a7_0.L AND p_1_a5.COL0 = __tmp_delta_ins_bt_for_d1_4_ar_a7_0.D )  ) AS p_0_a5_0   ) AS part_ins_d1_4_a5_0   ) AS __dummy__   ) AS tbl;

        insertion_data := (SELECT (array_to_json(detected_insertions))::text);
        IF insertion_data IS NOT DISTINCT FROM NULL THEN
            insertion_data := '[]';
        END IF;

        WITH __tmp_delta_ins_bt_for_d1_4_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size),
        __tmp_delta_del_bt_for_d1_4_ar as (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size)
        SELECT array_agg(tbl) INTO detected_deletions FROM (SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT part_del_d1_4_a5_0.COL0 AS COL0, part_del_d1_4_a5_0.COL1 AS COL1, part_del_d1_4_a5_0.COL2 AS COL2, part_del_d1_4_a5_0.COL3 AS COL3, part_del_d1_4_a5_0.COL4 AS COL4 FROM (SELECT p_0_a5_0.COL0 AS COL0, p_0_a5_0.COL1 AS COL1, p_0_a5_0.COL2 AS COL2, p_0_a5_0.COL3 AS COL3, p_0_a5_0.COL4 AS COL4 FROM (SELECT __tmp_delta_del_bt_for_d1_4_ar_a7_0.V AS COL0, __tmp_delta_del_bt_for_d1_4_ar_a7_0.L AS COL1, __tmp_delta_del_bt_for_d1_4_ar_a7_0.D AS COL2, __tmp_delta_del_bt_for_d1_4_ar_a7_0.R AS COL3, __tmp_delta_del_bt_for_d1_4_ar_a7_0.LINEAGE AS COL4 FROM __tmp_delta_del_bt_for_d1_4_ar AS __tmp_delta_del_bt_for_d1_4_ar_a7_0 WHERE __tmp_delta_del_bt_for_d1_4_ar_a7_0.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM (SELECT bt_a7_0.D AS COL0, bt_a7_0.L AS COL1, bt_a7_0.LINEAGE AS COL2, bt_a7_0.R AS COL3, bt_a7_0.V AS COL4 FROM public.bt AS bt_a7_0 WHERE bt_a7_0.AL1 = 'true'  ) AS p_1_a5 WHERE p_1_a5.COL4 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.V AND p_1_a5.COL3 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.R AND p_1_a5.COL2 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.LINEAGE AND p_1_a5.COL1 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.L AND p_1_a5.COL0 = __tmp_delta_del_bt_for_d1_4_ar_a7_0.D )  ) AS p_0_a5_0   ) AS part_del_d1_4_a5_0   ) AS __dummy__   ) AS tbl;

        deletion_data := (
        SELECT (array_to_json(detected_deletions))::text);
        IF deletion_data IS NOT DISTINCT FROM NULL THEN
            deletion_data := '[]';
        END IF;
        IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN
            user_name := (SELECT session_user);
            IF NOT (user_name = 'dejima') THEN
                xid := (SELECT txid_current());
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.d1_4"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
                result := public.d1_4_run_shell(json_data);
                IF result = 'true' THEN
                    DROP TABLE __tmp_delta_ins_bt_for_d1_4;
                    DROP TABLE __tmp_delta_del_bt_for_d1_4;
                ELSE
                    CREATE TEMPORARY TABLE IF NOT EXISTS dejima_abort_flag ON COMMIT DROP AS (SELECT true as finish);
                    RAISE LOG 'update on view is rejected by the external tool, result from running the sh script: %', result;
                    -- RAISE check_violation USING MESSAGE = 'update on view is rejected by the external tool, result from running the sh script: '
                    -- || result;
                END IF;
            ELSE
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;
                xid := (SELECT txid_current());

                -- update the table that stores the insertions and deletions we calculated
                -- DELETE FROM public.__dummy__d1_4_detected_deletions;
                INSERT INTO public.__dummy__d1_4_detected_deletions
                    ( SELECT xid, * FROM unnest(detected_deletions) as detected_deletions_alias );

                -- DELETE FROM public.__dummy__d1_4_detected_insertions;
                INSERT INTO public.__dummy__d1_4_detected_insertions
                    ( SELECT xid, * FROM unnest(detected_insertions) as detected_insertions_alias );
            END IF;
        END IF;
    END IF;
END IF;
RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.bt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the function public.bt_detect_update_on_d1_4() ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS bt_detect_update_on_d1_4 ON public.bt;
CREATE CONSTRAINT TRIGGER bt_detect_update_on_d1_4
    AFTER INSERT OR UPDATE OR DELETE ON
    public.bt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE public.bt_detect_update_on_d1_4();

CREATE OR REPLACE FUNCTION public.bt_propagate_updates_to_d1_4 ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS public.bt_detect_update_on_d1_4 IMMEDIATE;
    SET CONSTRAINTS public.bt_detect_update_on_d1_4 DEFERRED;
    DROP TABLE IF EXISTS bt_detect_update_on_d1_4_flag;
    DROP TABLE IF EXISTS __tmp_delta_del_bt_for_d1_4;
    DROP TABLE IF EXISTS __tmp_delta_ins_bt_for_d1_4;
    RETURN true;
  END;
$$;



CREATE OR REPLACE FUNCTION public.d1_4_delta_action()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  deletion_data text;
  insertion_data text;
  json_data text;
  result text;
  user_name text;
  xid int;
  delta_ins_size int;
  delta_del_size int;
  array_delta_del public.d1_4[];
  array_delta_ins public.d1_4[];
  temprec_delta_del_bt public.bt%ROWTYPE;
            array_delta_del_bt public.bt[];
temprec_delta_ins_bt public.bt%ROWTYPE;
            array_delta_ins_bt public.bt[];
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'd1_4_delta_action_flag') THEN
        -- RAISE LOG 'execute procedure d1_4_delta_action';
        CREATE TEMPORARY TABLE d1_4_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        IF EXISTS (SELECT WHERE false )
        THEN
          RAISE check_violation USING MESSAGE = 'Invalid view update: constraints on the view are violated';
        END IF;
        IF EXISTS (SELECT WHERE false )
        THEN
          RAISE check_violation USING MESSAGE = 'Invalid view update: constraints on the source relations are violated';
        END IF;
        SELECT array_agg(tbl) INTO array_delta_ins FROM __tmp_delta_ins_d1_4 AS tbl;
        SELECT array_agg(tbl) INTO array_delta_del FROM __tmp_delta_del_d1_4 as tbl;
        select count(*) INTO delta_ins_size FROM __tmp_delta_ins_d1_4;
        select count(*) INTO delta_del_size FROM __tmp_delta_del_d1_4;
        
            WITH __tmp_delta_del_d1_4_ar AS (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size),
            __tmp_delta_ins_d1_4_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size)
            SELECT array_agg(tbl) INTO array_delta_del_bt FROM (SELECT (ROW(COL0,COL1,COL2,COL3,COL4,COL5,COL6) :: public.bt).*
            FROM (SELECT delta_del_bt_a7_0.COL0 AS COL0, delta_del_bt_a7_0.COL1 AS COL1, delta_del_bt_a7_0.COL2 AS COL2, delta_del_bt_a7_0.COL3 AS COL3, delta_del_bt_a7_0.COL4 AS COL4, delta_del_bt_a7_0.COL5 AS COL5, delta_del_bt_a7_0.COL6 AS COL6 FROM (SELECT p_0_a7_0.COL0 AS COL0, p_0_a7_0.COL1 AS COL1, p_0_a7_0.COL2 AS COL2, p_0_a7_0.COL3 AS COL3, p_0_a7_0.COL4 AS COL4, p_0_a7_0.COL5 AS COL5, p_0_a7_0.COL6 AS COL6 FROM (SELECT bt_a7_1.V AS COL0, bt_a7_1.L AS COL1, bt_a7_1.D AS COL2, bt_a7_1.R AS COL3, bt_a7_1.AL2 AS COL4, bt_a7_1.AL1 AS COL5, bt_a7_1.LINEAGE AS COL6 FROM __tmp_delta_del_d1_4_ar AS __tmp_delta_del_d1_4_ar_a5_0, public.bt AS bt_a7_1 WHERE bt_a7_1.D = __tmp_delta_del_d1_4_ar_a5_0.D AND bt_a7_1.LINEAGE = __tmp_delta_del_d1_4_ar_a5_0.LINEAGE AND bt_a7_1.L = __tmp_delta_del_d1_4_ar_a5_0.L AND bt_a7_1.V = __tmp_delta_del_d1_4_ar_a5_0.V AND bt_a7_1.R = __tmp_delta_del_d1_4_ar_a5_0.R AND bt_a7_1.AL1 = 'true'  ) AS p_0_a7_0   ) AS delta_del_bt_a7_0   ) AS delta_del_bt_extra_alias) AS tbl;


            WITH __tmp_delta_del_d1_4_ar AS (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size),
            __tmp_delta_ins_d1_4_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size)
            SELECT array_agg(tbl) INTO array_delta_ins_bt FROM (SELECT (ROW(COL0,COL1,COL2,COL3,COL4,COL5,COL6) :: public.bt).*
            FROM (SELECT delta_ins_bt_a7_0.COL0 AS COL0, delta_ins_bt_a7_0.COL1 AS COL1, delta_ins_bt_a7_0.COL2 AS COL2, delta_ins_bt_a7_0.COL3 AS COL3, delta_ins_bt_a7_0.COL4 AS COL4, delta_ins_bt_a7_0.COL5 AS COL5, delta_ins_bt_a7_0.COL6 AS COL6 FROM (SELECT p_0_a7_0.COL0 AS COL0, p_0_a7_0.COL1 AS COL1, p_0_a7_0.COL2 AS COL2, p_0_a7_0.COL3 AS COL3, p_0_a7_0.COL4 AS COL4, p_0_a7_0.COL5 AS COL5, p_0_a7_0.COL6 AS COL6 FROM (SELECT __tmp_delta_ins_d1_4_ar_a5_0.V AS COL0, __tmp_delta_ins_d1_4_ar_a5_0.L AS COL1, __tmp_delta_ins_d1_4_ar_a5_0.D AS COL2, __tmp_delta_ins_d1_4_ar_a5_0.R AS COL3, 'false' AS COL4, 'true' AS COL5, __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AS COL6 FROM __tmp_delta_ins_d1_4_ar AS __tmp_delta_ins_d1_4_ar_a5_0 WHERE NOT EXISTS ( SELECT * FROM (SELECT bt_a7_1.V AS COL0, bt_a7_1.L AS COL1, bt_a7_1.D AS COL2, bt_a7_1.R AS COL3, bt_a7_0.AL2 AS COL4, 'true' AS COL5, bt_a7_1.LINEAGE AS COL6 FROM public.bt AS bt_a7_0, public.bt AS bt_a7_1 WHERE bt_a7_1.V = bt_a7_0.V AND bt_a7_1.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.LINEAGE = bt_a7_1.LINEAGE AND bt_a7.R = bt_a7_1.R AND bt_a7.D = bt_a7_1.D AND bt_a7.L = bt_a7_1.L AND bt_a7.V = bt_a7_1.V )  ) AS p_1_a7 WHERE p_1_a7.COL6 = __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AND p_1_a7.COL5 = 'true' AND p_1_a7.COL4 = 'false' AND p_1_a7.COL3 = __tmp_delta_ins_d1_4_ar_a5_0.R AND p_1_a7.COL2 = __tmp_delta_ins_d1_4_ar_a5_0.D AND p_1_a7.COL1 = __tmp_delta_ins_d1_4_ar_a5_0.L AND p_1_a7.COL0 = __tmp_delta_ins_d1_4_ar_a5_0.V ) AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.LINEAGE = __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AND bt_a7.R = __tmp_delta_ins_d1_4_ar_a5_0.R AND bt_a7.D = __tmp_delta_ins_d1_4_ar_a5_0.D AND bt_a7.L = __tmp_delta_ins_d1_4_ar_a5_0.L AND bt_a7.V = __tmp_delta_ins_d1_4_ar_a5_0.V ) AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.V = __tmp_delta_ins_d1_4_ar_a5_0.V )   UNION SELECT bt_a7_1.V AS COL0, __tmp_delta_ins_d1_4_ar_a5_0.L AS COL1, __tmp_delta_ins_d1_4_ar_a5_0.D AS COL2, __tmp_delta_ins_d1_4_ar_a5_0.R AS COL3, bt_a7_1.AL2 AS COL4, 'true' AS COL5, __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AS COL6 FROM __tmp_delta_ins_d1_4_ar AS __tmp_delta_ins_d1_4_ar_a5_0, public.bt AS bt_a7_1 WHERE bt_a7_1.V = __tmp_delta_ins_d1_4_ar_a5_0.V AND NOT EXISTS ( SELECT * FROM (SELECT bt_a7_0.V AS COL0, bt_a7_0.L AS COL1, bt_a7_0.D AS COL2, bt_a7_0.R AS COL3, 'false' AS COL4, 'true' AS COL5, bt_a7_0.LINEAGE AS COL6 FROM public.bt AS bt_a7_0 WHERE bt_a7_0.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.LINEAGE = bt_a7_0.LINEAGE AND bt_a7.R = bt_a7_0.R AND bt_a7.D = bt_a7_0.D AND bt_a7.L = bt_a7_0.L AND bt_a7.V = bt_a7_0.V ) AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.V = bt_a7_0.V )  ) AS p_3_a7 WHERE p_3_a7.COL6 = __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AND p_3_a7.COL5 = 'true' AND p_3_a7.COL4 = bt_a7_1.AL2 AND p_3_a7.COL3 = __tmp_delta_ins_d1_4_ar_a5_0.R AND p_3_a7.COL2 = __tmp_delta_ins_d1_4_ar_a5_0.D AND p_3_a7.COL1 = __tmp_delta_ins_d1_4_ar_a5_0.L AND p_3_a7.COL0 = bt_a7_1.V ) AND NOT EXISTS ( SELECT * FROM (SELECT bt_a7_1.V AS COL0, bt_a7_1.L AS COL1, bt_a7_1.D AS COL2, bt_a7_1.R AS COL3, bt_a7_0.AL2 AS COL4, 'true' AS COL5, bt_a7_1.LINEAGE AS COL6 FROM public.bt AS bt_a7_0, public.bt AS bt_a7_1 WHERE bt_a7_1.V = bt_a7_0.V AND bt_a7_1.AL1 = 'true' AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.LINEAGE = bt_a7_1.LINEAGE AND bt_a7.R = bt_a7_1.R AND bt_a7.D = bt_a7_1.D AND bt_a7.L = bt_a7_1.L AND bt_a7.V = bt_a7_1.V )  ) AS p_2_a7 WHERE p_2_a7.COL6 = __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AND p_2_a7.COL5 = 'true' AND p_2_a7.COL4 = bt_a7_1.AL2 AND p_2_a7.COL3 = __tmp_delta_ins_d1_4_ar_a5_0.R AND p_2_a7.COL2 = __tmp_delta_ins_d1_4_ar_a5_0.D AND p_2_a7.COL1 = __tmp_delta_ins_d1_4_ar_a5_0.L AND p_2_a7.COL0 = bt_a7_1.V ) AND NOT EXISTS ( SELECT * FROM public.bt AS bt_a7 WHERE bt_a7.LINEAGE = __tmp_delta_ins_d1_4_ar_a5_0.LINEAGE AND bt_a7.R = __tmp_delta_ins_d1_4_ar_a5_0.R AND bt_a7.D = __tmp_delta_ins_d1_4_ar_a5_0.D AND bt_a7.L = __tmp_delta_ins_d1_4_ar_a5_0.L AND bt_a7.V = bt_a7_1.V )  ) AS p_0_a7_0   ) AS delta_ins_bt_a7_0   ) AS delta_ins_bt_extra_alias) AS tbl; 


            IF array_delta_del_bt IS DISTINCT FROM NULL THEN
                FOREACH temprec_delta_del_bt IN array array_delta_del_bt  LOOP
                   DELETE FROM public.bt WHERE V = temprec_delta_del_bt.V AND L = temprec_delta_del_bt.L AND D = temprec_delta_del_bt.D AND R = temprec_delta_del_bt.R AND AL2 = temprec_delta_del_bt.AL2 AND AL1 = temprec_delta_del_bt.AL1 AND LINEAGE = temprec_delta_del_bt.LINEAGE;
                END LOOP;
            END IF;


            IF array_delta_ins_bt IS DISTINCT FROM NULL THEN
                INSERT INTO public.bt (SELECT * FROM unnest(array_delta_ins_bt) as array_delta_ins_bt_alias) ;
            END IF;

        insertion_data := (SELECT (array_to_json(array_delta_ins))::text);
        IF insertion_data IS NOT DISTINCT FROM NULL THEN
            insertion_data := '[]';
        END IF;
        deletion_data := (SELECT (array_to_json(array_delta_del))::text);
        IF deletion_data IS NOT DISTINCT FROM NULL THEN
            deletion_data := '[]';
        END IF;
        IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN
            user_name := (SELECT session_user);
            IF NOT (user_name = 'dejima') THEN
                xid := (SELECT txid_current());
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.d1_4"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
                result := public.d1_4_run_shell(json_data);
                IF NOT (result = 'true') THEN
                    CREATE TEMPORARY TABLE IF NOT EXISTS dejima_abort_flag ON COMMIT DROP AS (SELECT true as finish);
                    RAISE LOG 'update on view is rejected by the external tool, result from running the sh script: %', result;
                    -- RAISE check_violation USING MESSAGE = 'update on view is rejected by the external tool, result from running the sh script: '
                    -- || result;
                END IF;
            ELSE
                RAISE LOG 'function of detecting dejima update is called by % , no request sent to dejima proxy', user_name;
                xid := (SELECT txid_current());

                -- update the table that stores the insertions and deletions we calculated
                --DELETE FROM public.__dummy__d1_4_detected_deletions;
                INSERT INTO public.__dummy__d1_4_detected_deletions
                    SELECT xid, * FROM __tmp_delta_del_d1_4;

                --DELETE FROM public.__dummy__d1_4_detected_insertions;
                INSERT INTO public.__dummy__d1_4_detected_insertions
                    SELECT xid, * FROM __tmp_delta_ins_d1_4;
            END IF;
        END IF;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.d1_4';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.d1_4 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.d1_4_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__tmp_delta_ins_d1_4' OR table_name = '__tmp_delta_del_d1_4')
    THEN
        -- RAISE LOG 'execute procedure d1_4_materialization';
        CREATE TEMPORARY TABLE __tmp_delta_ins_d1_4 ( LIKE public.d1_4 ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __tmp_d1_4_trigger_delta_action_ins
        AFTER INSERT OR UPDATE OR DELETE ON
            __tmp_delta_ins_d1_4 DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE PROCEDURE public.d1_4_delta_action();

        CREATE TEMPORARY TABLE __tmp_delta_del_d1_4 ( LIKE public.d1_4 ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __tmp_d1_4_trigger_delta_action_del
        AFTER INSERT OR UPDATE OR DELETE ON
            __tmp_delta_del_d1_4 DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE PROCEDURE public.d1_4_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.d1_4';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.d1_4 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS d1_4_trigger_materialization ON public.d1_4;
CREATE TRIGGER d1_4_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.d1_4 FOR EACH STATEMENT EXECUTE PROCEDURE public.d1_4_materialization();

CREATE OR REPLACE FUNCTION public.d1_4_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE LOG 'execute procedure d1_4_update';
    IF TG_OP = 'INSERT' THEN
      -- RAISE LOG 'NEW: %', NEW;
      IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
        RAISE check_violation USING MESSAGE = 'Invalid update on view: view does not accept null value';
      END IF;
      DELETE FROM __tmp_delta_del_d1_4 WHERE ROW(V,L,D,R,LINEAGE) = NEW;
      INSERT INTO __tmp_delta_ins_d1_4 SELECT (NEW).*;
    ELSIF TG_OP = 'UPDATE' THEN
      IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
        RAISE check_violation USING MESSAGE = 'Invalid update on view: view does not accept null value';
      END IF;
      DELETE FROM __tmp_delta_ins_d1_4 WHERE ROW(V,L,D,R,LINEAGE) = OLD;
      INSERT INTO __tmp_delta_del_d1_4 SELECT (OLD).*;
      DELETE FROM __tmp_delta_del_d1_4 WHERE ROW(V,L,D,R,LINEAGE) = NEW;
      INSERT INTO __tmp_delta_ins_d1_4 SELECT (NEW).*;
    ELSIF TG_OP = 'DELETE' THEN
      -- RAISE LOG 'OLD: %', OLD;
      DELETE FROM __tmp_delta_ins_d1_4 WHERE ROW(V,L,D,R,LINEAGE) = OLD;
      INSERT INTO __tmp_delta_del_d1_4 SELECT (OLD).*;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.d1_4';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.d1_4 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS d1_4_trigger_update ON public.d1_4;
CREATE TRIGGER d1_4_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.d1_4 FOR EACH ROW EXECUTE PROCEDURE public.d1_4_update();

CREATE OR REPLACE FUNCTION public.d1_4_propagate_updates ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS __tmp_d1_4_trigger_delta_action_ins, __tmp_d1_4_trigger_delta_action_del IMMEDIATE;
    SET CONSTRAINTS __tmp_d1_4_trigger_delta_action_ins, __tmp_d1_4_trigger_delta_action_del DEFERRED;
    DROP TABLE IF EXISTS d1_4_delta_action_flag;
    DROP TABLE IF EXISTS __tmp_delta_del_d1_4;
    DROP TABLE IF EXISTS __tmp_delta_ins_d1_4;
    RETURN true;
  END;
$$;

