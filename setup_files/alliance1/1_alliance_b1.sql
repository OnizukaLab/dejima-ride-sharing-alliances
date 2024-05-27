
/*view definition (get):
b1(V, L, D, R, LINEAGE) :- p_0(V, L, D, R, LINEAGE).
p_0(V, L, D, R, LINEAGE) :- COL4' = 'B' , mt(V, L, D, R, COL4', COL5, LINEAGE).
*/

CREATE OR REPLACE VIEW public.b1 AS 
SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT b1_a5_0.COL0 AS COL0, b1_a5_0.COL1 AS COL1, b1_a5_0.COL2 AS COL2, b1_a5_0.COL3 AS COL3, b1_a5_0.COL4 AS COL4 FROM (SELECT p_0_a5_0.COL0 AS COL0, p_0_a5_0.COL1 AS COL1, p_0_a5_0.COL2 AS COL2, p_0_a5_0.COL3 AS COL3, p_0_a5_0.COL4 AS COL4 FROM (SELECT mt_a7_0.V AS COL0, mt_a7_0.L AS COL1, mt_a7_0.D AS COL2, mt_a7_0.R AS COL3, mt_a7_0.LINEAGE AS COL4 FROM public.mt AS mt_a7_0 WHERE mt_a7_0.P = 'B'  ) AS p_0_a5_0   ) AS b1_a5_0   ) AS __dummy__   ;

CREATE EXTENSION IF NOT EXISTS plsh;

CREATE TABLE IF NOT EXISTS public.__dummy__b1_detected_deletions (txid int, LIKE public.b1 );
CREATE INDEX IF NOT EXISTS idx__dummy__b1_detected_deletions ON public.__dummy__b1_detected_deletions (txid);
CREATE TABLE IF NOT EXISTS public.__dummy__b1_detected_insertions (txid int, LIKE public.b1 );
CREATE INDEX IF NOT EXISTS idx__dummy__b1_detected_insertions ON public.__dummy__b1_detected_insertions (txid);

CREATE OR REPLACE FUNCTION public.b1_get_detected_update_data(txid int)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  deletion_data text;
  insertion_data text;
  json_data text;
  BEGIN
    insertion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__b1_detected_insertions as t where t.txid = $1);
    IF insertion_data IS NOT DISTINCT FROM NULL THEN
        insertion_data := '[]';
    END IF;
    deletion_data := (SELECT (array_to_json(array_agg(t)))::text FROM public.__dummy__b1_detected_deletions as t where t.txid = $1);
    IF deletion_data IS NOT DISTINCT FROM NULL THEN
        deletion_data := '[]';
    END IF;
    IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN
        -- calcuate the update data
        json_data := concat('{"view": ' , '"public.b1"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
        -- clear the update data
        --DELETE FROM public.__dummy__b1_detected_deletions;
        --DELETE FROM public.__dummy__b1_detected_insertions;
    END IF;
    RETURN json_data;
  END;
$$;

CREATE OR REPLACE FUNCTION public.b1_run_shell(text) RETURNS text AS $$
#!/bin/sh

result=$(curl -s -X POST -H "Content-Type: application/json" $DEJIMA_EXECUTION_ENDPOINT -d "$1")
if  [ "$result" = "true" ];  then
    echo "true"
else 
    echo $result
fi
$$ LANGUAGE plsh;

CREATE OR REPLACE FUNCTION public.mt_materialization_for_b1()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
text_var1 text;
text_var2 text;
text_var3 text;
BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__tmp_delta_ins_mt_for_b1' OR table_name = '__tmp_delta_del_mt_for_b1')
    THEN
        -- RAISE LOG 'execute procedure mt_materialization_for_b1';
        CREATE TEMPORARY TABLE __tmp_delta_ins_mt_for_b1 ( LIKE public.mt ) WITH OIDS ON COMMIT DROP;
        CREATE TEMPORARY TABLE __tmp_delta_del_mt_for_b1 ( LIKE public.mt ) WITH OIDS ON COMMIT DROP;

    END IF;
    RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.mt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.mt ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS mt_trigger_materialization_for_b1 ON public.mt;
CREATE TRIGGER mt_trigger_materialization_for_b1
    BEFORE INSERT OR UPDATE OR DELETE ON
    public.mt FOR EACH STATEMENT EXECUTE PROCEDURE public.mt_materialization_for_b1();

CREATE OR REPLACE FUNCTION public.mt_update_for_b1()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
text_var1 text;
text_var2 text;
text_var3 text;
BEGIN
    -- RAISE LOG 'execute procedure mt_update_for_b1';
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'b1_delta_action_flag') THEN
        IF TG_OP = 'INSERT' THEN
        -- RAISE LOG 'NEW: %', NEW;
        IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
            RAISE check_violation USING MESSAGE = 'Invalid update: null value is not accepted';
        END IF;
        DELETE FROM __tmp_delta_del_mt_for_b1 WHERE ROW(V,L,D,R,P,U,LINEAGE)= NEW;
        INSERT INTO __tmp_delta_ins_mt_for_b1 SELECT (NEW).*;
        ELSIF TG_OP = 'UPDATE' THEN
        IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
            RAISE check_violation USING MESSAGE = 'Invalid update: null value is not accepted';
        END IF;
        DELETE FROM __tmp_delta_ins_mt_for_b1 WHERE ROW(V,L,D,R,P,U,LINEAGE) = OLD;
        INSERT INTO __tmp_delta_del_mt_for_b1 SELECT (OLD).*;
        DELETE FROM __tmp_delta_del_mt_for_b1 WHERE ROW(V,L,D,R,P,U,LINEAGE) = NEW;
        INSERT INTO __tmp_delta_ins_mt_for_b1 SELECT (NEW).*;
        ELSIF TG_OP = 'DELETE' THEN
        -- RAISE LOG 'OLD: %', OLD;
        DELETE FROM __tmp_delta_ins_mt_for_b1 WHERE ROW(V,L,D,R,P,U,LINEAGE) = OLD;
        INSERT INTO __tmp_delta_del_mt_for_b1 SELECT (OLD).*;
        END IF;
    END IF;
    RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.mt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.mt ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS mt_trigger_update_for_b1 ON public.mt;
CREATE TRIGGER mt_trigger_update_for_b1
    AFTER INSERT OR UPDATE OR DELETE ON
    public.mt FOR EACH ROW EXECUTE PROCEDURE public.mt_update_for_b1();

CREATE OR REPLACE FUNCTION public.mt_detect_update_on_b1()
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
array_delta_del public.mt[];
array_delta_ins public.mt[];
detected_deletions public.b1[];
detected_insertions public.b1[];
delta_ins_size int;
delta_del_size int;
BEGIN
IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'mt_detect_update_on_b1_flag') THEN
    CREATE TEMPORARY TABLE mt_detect_update_on_b1_flag ON COMMIT DROP AS (SELECT true as finish);
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'b1_delta_action_flag') THEN
        SELECT array_agg(tbl) INTO array_delta_ins FROM __tmp_delta_ins_mt_for_b1 AS tbl;
        select count(*) INTO delta_ins_size FROM __tmp_delta_ins_mt_for_b1;
        SELECT array_agg(tbl) INTO array_delta_del FROM __tmp_delta_del_mt_for_b1 tbl;
        select count(*) INTO delta_del_size FROM __tmp_delta_del_mt_for_b1;

        WITH __tmp_delta_ins_mt_for_b1_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size),
        __tmp_delta_del_mt_for_b1_ar as (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size)
        SELECT array_agg(tbl) INTO detected_insertions FROM (SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT part_ins_b1_a5_0.COL0 AS COL0, part_ins_b1_a5_0.COL1 AS COL1, part_ins_b1_a5_0.COL2 AS COL2, part_ins_b1_a5_0.COL3 AS COL3, part_ins_b1_a5_0.COL4 AS COL4 FROM (SELECT p_0_a5_0.COL0 AS COL0, p_0_a5_0.COL1 AS COL1, p_0_a5_0.COL2 AS COL2, p_0_a5_0.COL3 AS COL3, p_0_a5_0.COL4 AS COL4 FROM (SELECT __tmp_delta_ins_mt_for_b1_ar_a7_0.V AS COL0, __tmp_delta_ins_mt_for_b1_ar_a7_0.L AS COL1, __tmp_delta_ins_mt_for_b1_ar_a7_0.D AS COL2, __tmp_delta_ins_mt_for_b1_ar_a7_0.R AS COL3, __tmp_delta_ins_mt_for_b1_ar_a7_0.LINEAGE AS COL4 FROM __tmp_delta_ins_mt_for_b1_ar AS __tmp_delta_ins_mt_for_b1_ar_a7_0 WHERE __tmp_delta_ins_mt_for_b1_ar_a7_0.P = 'B' AND NOT EXISTS ( SELECT * FROM (SELECT __tmp_delta_ins_mt_for_b1_ar_a7_1.D AS COL0, __tmp_delta_ins_mt_for_b1_ar_a7_1.L AS COL1, __tmp_delta_ins_mt_for_b1_ar_a7_1.LINEAGE AS COL2, __tmp_delta_ins_mt_for_b1_ar_a7_1.R AS COL3, __tmp_delta_ins_mt_for_b1_ar_a7_1.V AS COL4 FROM __tmp_delta_del_mt_for_b1_ar AS __tmp_delta_del_mt_for_b1_ar_a7_0, __tmp_delta_ins_mt_for_b1_ar AS __tmp_delta_ins_mt_for_b1_ar_a7_1 WHERE __tmp_delta_ins_mt_for_b1_ar_a7_1.U = __tmp_delta_del_mt_for_b1_ar_a7_0.U AND __tmp_delta_ins_mt_for_b1_ar_a7_1.L = __tmp_delta_del_mt_for_b1_ar_a7_0.L AND __tmp_delta_ins_mt_for_b1_ar_a7_1.R = __tmp_delta_del_mt_for_b1_ar_a7_0.R AND __tmp_delta_ins_mt_for_b1_ar_a7_1.V = __tmp_delta_del_mt_for_b1_ar_a7_0.V AND __tmp_delta_ins_mt_for_b1_ar_a7_1.D = __tmp_delta_del_mt_for_b1_ar_a7_0.D AND __tmp_delta_ins_mt_for_b1_ar_a7_1.LINEAGE = __tmp_delta_del_mt_for_b1_ar_a7_0.LINEAGE AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = __tmp_delta_del_mt_for_b1_ar_a7_0.P AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = 'B' AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = 'B'   UNION SELECT __tmp_delta_ins_mt_for_b1_ar_a7_1.D AS COL0, __tmp_delta_ins_mt_for_b1_ar_a7_1.L AS COL1, __tmp_delta_ins_mt_for_b1_ar_a7_1.LINEAGE AS COL2, __tmp_delta_ins_mt_for_b1_ar_a7_1.R AS COL3, __tmp_delta_ins_mt_for_b1_ar_a7_1.V AS COL4 FROM public.mt AS mt_a7_0, __tmp_delta_ins_mt_for_b1_ar AS __tmp_delta_ins_mt_for_b1_ar_a7_1 WHERE __tmp_delta_ins_mt_for_b1_ar_a7_1.U = mt_a7_0.U AND __tmp_delta_ins_mt_for_b1_ar_a7_1.L = mt_a7_0.L AND __tmp_delta_ins_mt_for_b1_ar_a7_1.R = mt_a7_0.R AND __tmp_delta_ins_mt_for_b1_ar_a7_1.V = mt_a7_0.V AND __tmp_delta_ins_mt_for_b1_ar_a7_1.D = mt_a7_0.D AND __tmp_delta_ins_mt_for_b1_ar_a7_1.LINEAGE = mt_a7_0.LINEAGE AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = mt_a7_0.P AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = 'B' AND __tmp_delta_ins_mt_for_b1_ar_a7_1.P = 'B' AND NOT EXISTS ( SELECT * FROM (SELECT __tmp_delta_ins_mt_for_b1_ar_a7_0.P AS COL0, __tmp_delta_ins_mt_for_b1_ar_a7_0.U AS COL1, __tmp_delta_ins_mt_for_b1_ar_a7_0.D AS COL2, __tmp_delta_ins_mt_for_b1_ar_a7_0.L AS COL3, __tmp_delta_ins_mt_for_b1_ar_a7_0.LINEAGE AS COL4, __tmp_delta_ins_mt_for_b1_ar_a7_0.R AS COL5, __tmp_delta_ins_mt_for_b1_ar_a7_0.V AS COL6 FROM __tmp_delta_ins_mt_for_b1_ar AS __tmp_delta_ins_mt_for_b1_ar_a7_0 WHERE __tmp_delta_ins_mt_for_b1_ar_a7_0.P = 'B'  ) AS p_2_a7 WHERE p_2_a7.COL6 = __tmp_delta_ins_mt_for_b1_ar_a7_1.V AND p_2_a7.COL5 = __tmp_delta_ins_mt_for_b1_ar_a7_1.R AND p_2_a7.COL4 = __tmp_delta_ins_mt_for_b1_ar_a7_1.LINEAGE AND p_2_a7.COL3 = __tmp_delta_ins_mt_for_b1_ar_a7_1.L AND p_2_a7.COL2 = __tmp_delta_ins_mt_for_b1_ar_a7_1.D AND p_2_a7.COL1 = __tmp_delta_ins_mt_for_b1_ar_a7_1.U AND p_2_a7.COL0 = __tmp_delta_ins_mt_for_b1_ar_a7_1.P )  ) AS p_1_a5 WHERE p_1_a5.COL4 = __tmp_delta_ins_mt_for_b1_ar_a7_0.V AND p_1_a5.COL3 = __tmp_delta_ins_mt_for_b1_ar_a7_0.R AND p_1_a5.COL2 = __tmp_delta_ins_mt_for_b1_ar_a7_0.LINEAGE AND p_1_a5.COL1 = __tmp_delta_ins_mt_for_b1_ar_a7_0.L AND p_1_a5.COL0 = __tmp_delta_ins_mt_for_b1_ar_a7_0.D )  ) AS p_0_a5_0   ) AS part_ins_b1_a5_0   ) AS __dummy__   ) AS tbl;

        insertion_data := (SELECT (array_to_json(detected_insertions))::text);
        IF insertion_data IS NOT DISTINCT FROM NULL THEN
            insertion_data := '[]';
        END IF;

        WITH __tmp_delta_ins_mt_for_b1_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size),
        __tmp_delta_del_mt_for_b1_ar as (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size)
        SELECT array_agg(tbl) INTO detected_deletions FROM (SELECT __dummy__.COL0 AS V, __dummy__.COL1 AS L, __dummy__.COL2 AS D, __dummy__.COL3 AS R, __dummy__.COL4 AS LINEAGE FROM (SELECT part_del_b1_a5_0.COL0 AS COL0, part_del_b1_a5_0.COL1 AS COL1, part_del_b1_a5_0.COL2 AS COL2, part_del_b1_a5_0.COL3 AS COL3, part_del_b1_a5_0.COL4 AS COL4 FROM (SELECT p_0_a5_0.COL0 AS COL0, p_0_a5_0.COL1 AS COL1, p_0_a5_0.COL2 AS COL2, p_0_a5_0.COL3 AS COL3, p_0_a5_0.COL4 AS COL4 FROM (SELECT __tmp_delta_del_mt_for_b1_ar_a7_0.V AS COL0, __tmp_delta_del_mt_for_b1_ar_a7_0.L AS COL1, __tmp_delta_del_mt_for_b1_ar_a7_0.D AS COL2, __tmp_delta_del_mt_for_b1_ar_a7_0.R AS COL3, __tmp_delta_del_mt_for_b1_ar_a7_0.LINEAGE AS COL4 FROM __tmp_delta_del_mt_for_b1_ar AS __tmp_delta_del_mt_for_b1_ar_a7_0 WHERE __tmp_delta_del_mt_for_b1_ar_a7_0.P = 'B' AND NOT EXISTS ( SELECT * FROM (SELECT mt_a7_0.D AS COL0, mt_a7_0.L AS COL1, mt_a7_0.LINEAGE AS COL2, mt_a7_0.R AS COL3, mt_a7_0.V AS COL4 FROM public.mt AS mt_a7_0 WHERE mt_a7_0.P = 'B'  ) AS p_1_a5 WHERE p_1_a5.COL4 = __tmp_delta_del_mt_for_b1_ar_a7_0.V AND p_1_a5.COL3 = __tmp_delta_del_mt_for_b1_ar_a7_0.R AND p_1_a5.COL2 = __tmp_delta_del_mt_for_b1_ar_a7_0.LINEAGE AND p_1_a5.COL1 = __tmp_delta_del_mt_for_b1_ar_a7_0.L AND p_1_a5.COL0 = __tmp_delta_del_mt_for_b1_ar_a7_0.D )  ) AS p_0_a5_0   ) AS part_del_b1_a5_0   ) AS __dummy__   ) AS tbl;

        deletion_data := (
        SELECT (array_to_json(detected_deletions))::text);
        IF deletion_data IS NOT DISTINCT FROM NULL THEN
            deletion_data := '[]';
        END IF;
        IF (insertion_data IS DISTINCT FROM '[]') OR (deletion_data IS DISTINCT FROM '[]') THEN
            user_name := (SELECT session_user);
            IF NOT (user_name = 'dejima') THEN
                xid := (SELECT txid_current());
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.b1"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
                result := public.b1_run_shell(json_data);
                IF result = 'true' THEN
                    DROP TABLE __tmp_delta_ins_mt_for_b1;
                    DROP TABLE __tmp_delta_del_mt_for_b1;
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
                -- DELETE FROM public.__dummy__b1_detected_deletions;
                INSERT INTO public.__dummy__b1_detected_deletions
                    ( SELECT xid, * FROM unnest(detected_deletions) as detected_deletions_alias );

                -- DELETE FROM public.__dummy__b1_detected_insertions;
                INSERT INTO public.__dummy__b1_detected_insertions
                    ( SELECT xid, * FROM unnest(detected_insertions) as detected_insertions_alias );
            END IF;
        END IF;
    END IF;
END IF;
RETURN NULL;
EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to public.mt';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the function public.mt_detect_update_on_b1() ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS mt_detect_update_on_b1 ON public.mt;
CREATE CONSTRAINT TRIGGER mt_detect_update_on_b1
    AFTER INSERT OR UPDATE OR DELETE ON
    public.mt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE public.mt_detect_update_on_b1();

CREATE OR REPLACE FUNCTION public.mt_propagate_updates_to_b1 ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS public.mt_detect_update_on_b1 IMMEDIATE;
    SET CONSTRAINTS public.mt_detect_update_on_b1 DEFERRED;
    DROP TABLE IF EXISTS mt_detect_update_on_b1_flag;
    RETURN true;
  END;
$$;



CREATE OR REPLACE FUNCTION public.b1_delta_action()
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
  array_delta_del public.b1[];
  array_delta_ins public.b1[];
  temprec_delta_del_mt public.mt%ROWTYPE;
            array_delta_del_mt public.mt[];
temprec_delta_ins_mt public.mt%ROWTYPE;
            array_delta_ins_mt public.mt[];
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'b1_delta_action_flag') THEN
        -- RAISE LOG 'execute procedure b1_delta_action';
        CREATE TEMPORARY TABLE b1_delta_action_flag ON COMMIT DROP AS (SELECT true as finish);
        IF EXISTS (SELECT WHERE false )
        THEN
          RAISE check_violation USING MESSAGE = 'Invalid view update: constraints on the view are violated';
        END IF;
        IF EXISTS (SELECT WHERE false )
        THEN
          RAISE check_violation USING MESSAGE = 'Invalid view update: constraints on the source relations are violated';
        END IF;
        SELECT array_agg(tbl) INTO array_delta_ins FROM __tmp_delta_ins_b1 AS tbl;
        SELECT array_agg(tbl) INTO array_delta_del FROM __tmp_delta_del_b1 as tbl;
        select count(*) INTO delta_ins_size FROM __tmp_delta_ins_b1;
        select count(*) INTO delta_del_size FROM __tmp_delta_del_b1;
        
            WITH __tmp_delta_del_b1_ar AS (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size),
            __tmp_delta_ins_b1_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size)
            SELECT array_agg(tbl) INTO array_delta_del_mt FROM (SELECT (ROW(COL0,COL1,COL2,COL3,COL4,COL5,COL6) :: public.mt).*
            FROM (SELECT delta_del_mt_a7_0.COL0 AS COL0, delta_del_mt_a7_0.COL1 AS COL1, delta_del_mt_a7_0.COL2 AS COL2, delta_del_mt_a7_0.COL3 AS COL3, delta_del_mt_a7_0.COL4 AS COL4, delta_del_mt_a7_0.COL5 AS COL5, delta_del_mt_a7_0.COL6 AS COL6 FROM (SELECT mt_a7_0.V AS COL0, mt_a7_0.L AS COL1, mt_a7_0.D AS COL2, mt_a7_0.R AS COL3, mt_a7_0.P AS COL4, mt_a7_0.U AS COL5, mt_a7_0.LINEAGE AS COL6 FROM public.mt AS mt_a7_0 WHERE mt_a7_0.P = 'B' AND NOT EXISTS ( SELECT * FROM (SELECT b1_a5_0.V AS COL0, b1_a5_0.L AS COL1, b1_a5_0.D AS COL2, b1_a5_0.R AS COL3, b1_a5_0.LINEAGE AS COL4 FROM public.b1 AS b1_a5_0 WHERE NOT EXISTS ( SELECT * FROM __tmp_delta_del_b1_ar AS __tmp_delta_del_b1_ar_a5 WHERE __tmp_delta_del_b1_ar_a5.LINEAGE = b1_a5_0.LINEAGE AND __tmp_delta_del_b1_ar_a5.R = b1_a5_0.R AND __tmp_delta_del_b1_ar_a5.D = b1_a5_0.D AND __tmp_delta_del_b1_ar_a5.L = b1_a5_0.L AND __tmp_delta_del_b1_ar_a5.V = b1_a5_0.V )   UNION SELECT __tmp_delta_ins_b1_ar_a5_0.V AS COL0, __tmp_delta_ins_b1_ar_a5_0.L AS COL1, __tmp_delta_ins_b1_ar_a5_0.D AS COL2, __tmp_delta_ins_b1_ar_a5_0.R AS COL3, __tmp_delta_ins_b1_ar_a5_0.LINEAGE AS COL4 FROM __tmp_delta_ins_b1_ar AS __tmp_delta_ins_b1_ar_a5_0   ) AS new_b1_a5 WHERE new_b1_a5.COL4 = mt_a7_0.LINEAGE AND new_b1_a5.COL3 = mt_a7_0.R AND new_b1_a5.COL2 = mt_a7_0.D AND new_b1_a5.COL1 = mt_a7_0.L AND new_b1_a5.COL0 = mt_a7_0.V )  ) AS delta_del_mt_a7_0   ) AS delta_del_mt_extra_alias) AS tbl;


            WITH __tmp_delta_del_b1_ar AS (SELECT * FROM unnest(array_delta_del) as array_delta_del_alias limit delta_del_size),
            __tmp_delta_ins_b1_ar as (SELECT * FROM unnest(array_delta_ins) as array_delta_ins_alias limit delta_ins_size)
            SELECT array_agg(tbl) INTO array_delta_ins_mt FROM (SELECT (ROW(COL0,COL1,COL2,COL3,COL4,COL5,COL6) :: public.mt).*
            FROM (SELECT delta_ins_mt_a7_0.COL0 AS COL0, delta_ins_mt_a7_0.COL1 AS COL1, delta_ins_mt_a7_0.COL2 AS COL2, delta_ins_mt_a7_0.COL3 AS COL3, delta_ins_mt_a7_0.COL4 AS COL4, delta_ins_mt_a7_0.COL5 AS COL5, delta_ins_mt_a7_0.COL6 AS COL6 FROM (SELECT new_b1_a5_0.COL0 AS COL0, new_b1_a5_0.COL1 AS COL1, new_b1_a5_0.COL2 AS COL2, new_b1_a5_0.COL3 AS COL3, 'B' AS COL4, 'true' AS COL5, new_b1_a5_0.COL4 AS COL6 FROM (SELECT b1_a5_0.V AS COL0, b1_a5_0.L AS COL1, b1_a5_0.D AS COL2, b1_a5_0.R AS COL3, b1_a5_0.LINEAGE AS COL4 FROM public.b1 AS b1_a5_0 WHERE NOT EXISTS ( SELECT * FROM __tmp_delta_del_b1_ar AS __tmp_delta_del_b1_ar_a5 WHERE __tmp_delta_del_b1_ar_a5.LINEAGE = b1_a5_0.LINEAGE AND __tmp_delta_del_b1_ar_a5.R = b1_a5_0.R AND __tmp_delta_del_b1_ar_a5.D = b1_a5_0.D AND __tmp_delta_del_b1_ar_a5.L = b1_a5_0.L AND __tmp_delta_del_b1_ar_a5.V = b1_a5_0.V )   UNION SELECT __tmp_delta_ins_b1_ar_a5_0.V AS COL0, __tmp_delta_ins_b1_ar_a5_0.L AS COL1, __tmp_delta_ins_b1_ar_a5_0.D AS COL2, __tmp_delta_ins_b1_ar_a5_0.R AS COL3, __tmp_delta_ins_b1_ar_a5_0.LINEAGE AS COL4 FROM __tmp_delta_ins_b1_ar AS __tmp_delta_ins_b1_ar_a5_0   ) AS new_b1_a5_0 WHERE NOT EXISTS ( SELECT * FROM public.mt AS mt_a7 WHERE mt_a7.LINEAGE = new_b1_a5_0.COL4 AND mt_a7.P = 'B' AND mt_a7.R = new_b1_a5_0.COL3 AND mt_a7.D = new_b1_a5_0.COL2 AND mt_a7.L = new_b1_a5_0.COL1 AND mt_a7.V = new_b1_a5_0.COL0 )  ) AS delta_ins_mt_a7_0   ) AS delta_ins_mt_extra_alias) AS tbl; 


            IF array_delta_del_mt IS DISTINCT FROM NULL THEN
                FOREACH temprec_delta_del_mt IN array array_delta_del_mt  LOOP
                   DELETE FROM public.mt WHERE V = temprec_delta_del_mt.V AND L = temprec_delta_del_mt.L AND D = temprec_delta_del_mt.D AND R = temprec_delta_del_mt.R AND P = temprec_delta_del_mt.P AND U = temprec_delta_del_mt.U AND LINEAGE = temprec_delta_del_mt.LINEAGE;
                END LOOP;
            END IF;


            IF array_delta_ins_mt IS DISTINCT FROM NULL THEN
                INSERT INTO public.mt (SELECT * FROM unnest(array_delta_ins_mt) as array_delta_ins_mt_alias) ;
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
                json_data := concat('{"xid": "', xid, '" , "view": ' , '"public.b1"', ', ' , '"insertions": ' , insertion_data , ', ' , '"deletions": ' , deletion_data , '}');
                result := public.b1_run_shell(json_data);
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
                --DELETE FROM public.__dummy__b1_detected_deletions;
                INSERT INTO public.__dummy__b1_detected_deletions
                    SELECT xid, * FROM __tmp_delta_del_b1;

                --DELETE FROM public.__dummy__b1_detected_insertions;
                INSERT INTO public.__dummy__b1_detected_insertions
                    SELECT xid, * FROM __tmp_delta_ins_b1;
            END IF;
        END IF;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.b1';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.b1 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

CREATE OR REPLACE FUNCTION public.b1_materialization()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '__tmp_delta_ins_b1' OR table_name = '__tmp_delta_del_b1')
    THEN
        -- RAISE LOG 'execute procedure b1_materialization';
        CREATE TEMPORARY TABLE __tmp_delta_ins_b1 ( LIKE public.b1 ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __tmp_b1_trigger_delta_action_ins
        AFTER INSERT OR UPDATE OR DELETE ON
            __tmp_delta_ins_b1 DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE PROCEDURE public.b1_delta_action();

        CREATE TEMPORARY TABLE __tmp_delta_del_b1 ( LIKE public.b1 ) WITH OIDS ON COMMIT DROP;
        CREATE CONSTRAINT TRIGGER __tmp_b1_trigger_delta_action_del
        AFTER INSERT OR UPDATE OR DELETE ON
            __tmp_delta_del_b1 DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE PROCEDURE public.b1_delta_action();
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.b1';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.b1 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS b1_trigger_materialization ON public.b1;
CREATE TRIGGER b1_trigger_materialization
    BEFORE INSERT OR UPDATE OR DELETE ON
      public.b1 FOR EACH STATEMENT EXECUTE PROCEDURE public.b1_materialization();

CREATE OR REPLACE FUNCTION public.b1_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  DECLARE
  text_var1 text;
  text_var2 text;
  text_var3 text;
  BEGIN
    -- RAISE LOG 'execute procedure b1_update';
    IF TG_OP = 'INSERT' THEN
      -- RAISE LOG 'NEW: %', NEW;
      IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
        RAISE check_violation USING MESSAGE = 'Invalid update on view: view does not accept null value';
      END IF;
      DELETE FROM __tmp_delta_del_b1 WHERE ROW(V,L,D,R,LINEAGE) = NEW;
      INSERT INTO __tmp_delta_ins_b1 SELECT (NEW).*;
    ELSIF TG_OP = 'UPDATE' THEN
      IF (SELECT count(*) FILTER (WHERE j.value = jsonb 'null') FROM  jsonb_each(to_jsonb(NEW)) j) > 0 THEN
        RAISE check_violation USING MESSAGE = 'Invalid update on view: view does not accept null value';
      END IF;
      DELETE FROM __tmp_delta_ins_b1 WHERE ROW(V,L,D,R,LINEAGE) = OLD;
      INSERT INTO __tmp_delta_del_b1 SELECT (OLD).*;
      DELETE FROM __tmp_delta_del_b1 WHERE ROW(V,L,D,R,LINEAGE) = NEW;
      INSERT INTO __tmp_delta_ins_b1 SELECT (NEW).*;
    ELSIF TG_OP = 'DELETE' THEN
      -- RAISE LOG 'OLD: %', OLD;
      DELETE FROM __tmp_delta_ins_b1 WHERE ROW(V,L,D,R,LINEAGE) = OLD;
      INSERT INTO __tmp_delta_del_b1 SELECT (OLD).*;
    END IF;
    RETURN NULL;
  EXCEPTION
    WHEN object_not_in_prerequisite_state THEN
        RAISE object_not_in_prerequisite_state USING MESSAGE = 'no permission to insert or delete or update to source relations of public.b1';
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS text_var1 = RETURNED_SQLSTATE,
                                text_var2 = PG_EXCEPTION_DETAIL,
                                text_var3 = MESSAGE_TEXT;
        RAISE SQLSTATE 'DA000' USING MESSAGE = 'error on the trigger of public.b1 ; error code: ' || text_var1 || ' ; ' || text_var2 ||' ; ' || text_var3;
        RETURN NULL;
  END;
$$;

DROP TRIGGER IF EXISTS b1_trigger_update ON public.b1;
CREATE TRIGGER b1_trigger_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON
      public.b1 FOR EACH ROW EXECUTE PROCEDURE public.b1_update();

CREATE OR REPLACE FUNCTION public.b1_propagate_updates ()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
  BEGIN
    SET CONSTRAINTS __tmp_b1_trigger_delta_action_ins, __tmp_b1_trigger_delta_action_del IMMEDIATE;
    SET CONSTRAINTS __tmp_b1_trigger_delta_action_ins, __tmp_b1_trigger_delta_action_del DEFERRED;
    DROP TABLE IF EXISTS b1_delta_action_flag;
    DROP TABLE IF EXISTS __tmp_delta_del_b1;
    DROP TABLE IF EXISTS __tmp_delta_ins_b1;
    RETURN true;
  END;
$$;

