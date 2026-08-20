#!/bin/zsh

#SOURCED FROM
#https://zwbetz.com/connect-to-a-postgresql-database-and-run-a-query-from-a-bash-script/

#open
set -o allexport
source sql.env
set +o allexport
#close

psql -f test_query.sql

