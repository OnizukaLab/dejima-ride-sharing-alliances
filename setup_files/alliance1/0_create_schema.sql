DROP TABLE IF EXISTS mt;
CREATE TABLE mt(
    V int,
    L int,
    D int,
    R int,
    P varchar,
    U varchar,
    LINEAGE	varchar
);

CREATE VIEW uv AS SELECT V, U FROM mt WHERE U = 'true';

CREATE INDEX ON mt (lineage);