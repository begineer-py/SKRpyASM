#!/bin/bash
set -e
# Postgres 官方映像已依 POSTGRES_USER / POSTGRES_DB 環境變數建立超級使用者與其擁有的資料庫，
# 故此處毋須再以 SQL 建立使用者或資料庫（否則於乾淨 volume 上會以
# "role already exists" / "database already exists" 於 set -e 下崩潰）。
# Docker 模式的覆寫由 docker/docker-compose.yml 的 environment: 區塊負責。
echo "DB init: user/db created by POSTGRES_USER/POSTGRES_DB env (compose environment: block)"
