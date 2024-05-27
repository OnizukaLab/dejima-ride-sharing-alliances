DROP TABLE IF EXISTS bt;
CREATE TABLE bt(
    V int,
    L int,
    D int,
    R int,
    U varchar,
    LINEAGE	varchar
);

CREATE VIEW uv AS SELECT V, U FROM bt WHERE U = 'true';

CREATE INDEX ON bt (lineage);