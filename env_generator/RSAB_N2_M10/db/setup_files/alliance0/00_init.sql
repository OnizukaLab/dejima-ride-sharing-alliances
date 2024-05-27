DROP TABLE IF EXISTS mt;
CREATE TABLE mt(
    V serial,
    L int,
    D int,
    R int,
    A int,
    LINEAGE	varchar,
    primary key (V, A)
);

CREATE INDEX ON mt (lineage);
