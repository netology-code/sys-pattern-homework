#!/bin/bash

NUMBER_OF_BACKUP_COPIES=5

SOURCE_DIRECTORY=~/

BACKUP_SERVER_IP="10.129.0.15"
BACKUP_SERVER_USER="virtualubu"
BACKUP_DIRECTORY="/tmp/backup"

LATEST_BACKUP_LINK="${BACKUP_DIRECTORY}/latest"

CURRENT_TIME=`date +%Y-%m-%d_%T`

DESTINATION_PATH="${BACKUP_DIRECTORY}/${CURRENT_TIME}"
DESTINATION_FULL_PATH="${BACKUP_SERVER_USER}@${BACKUP_SERVER_IP}:${DESTINATION_PATH}"


rsync -a --delete "${SOURCE_DIRECTORY}" --link-dest "${LATEST_BACKUP_LINK}" "${DESTINATION_FULL_PATH}"

backup_status=$?

if [ $backup_status -eq 0 ]; then

    ssh "${BACKUP_SERVER_USER}@${BACKUP_SERVER_IP}" "rm -rf ${LATEST_BACKUP_LINK}; \
        ln -s ${DESTINATION_PATH} ${LATEST_BACKUP_LINK}"

    backup_status=$?

    if [ $backup_status -eq 0 ]; then
        logger [${BASH_SOURCE}] Backup is successful
    fi

else
    logger [${BASH_SOURCE}] Backup failed
fi

ssh "${BACKUP_SERVER_USER}@${BACKUP_SERVER_IP}" "ls -d ${BACKUP_DIRECTORY}/*| head -n -$((NUMBER_OF_BACKUP_COPIES+1)) | xargs rm -rf"

exit $backup_status