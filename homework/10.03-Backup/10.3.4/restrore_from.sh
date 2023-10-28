#!/bin/bash

BACKUP_SERVER_IP="10.129.0.15"
BACKUP_SERVER_USER="virtualubu"
BACKUP_DIRECTORY="/tmp/backup"

LATEST_BACKUP_LINK="${BACKUP_DIRECTORY}/latest"

DIRECTORY_TO_RESTORE=~/

backups=($(ssh ${BACKUP_SERVER_USER}@${BACKUP_SERVER_IP} "ls ${BACKUP_DIRECTORY}"))

PS3="Выберите номер требуемого бэкапа: "
select backup in "${backups[@]}"; do
    
    if [[ ! " ${backups[*]} " =~ " ${backup} " ]]; then
        break
    fi

    rsync -a --delete "${BACKUP_SERVER_USER}@${BACKUP_SERVER_IP}:${BACKUP_DIRECTORY}/${backup}/" "${DIRECTORY_TO_RESTORE}"

    restore_status=$?

    if [ $restore_status -eq 0 ]; then
        logger [${BASH_SOURCE}] Backup restore is successful
        echo "Файлы успешно восстановлены из бэкапа ${backup}"
    else
        logger [${BASH_SOURCE}] Backup restore failed
        echo "Не удалось восстановить файлы"
    fi

    exit $restore_status
done
