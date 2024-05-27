DROP TABLE IF EXISTS mt;
CREATE TABLE mt(
    V serial primary key,
    L int,
    D int,
    R int,
    P int,
    LINEAGE	varchar
);

CREATE INDEX ON mt (lineage);
