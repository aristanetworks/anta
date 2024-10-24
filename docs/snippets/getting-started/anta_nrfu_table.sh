anta nrfu \
    --username arista \
    --password $LABPASSPHRASE \
    --inventory ./inventory.yml \
    `# uncomment the two next lines if you have an enable password` \
    `# --enable` \
    `# --enable-password <password>` \
    --catalog ./catalog.yml \
    `# table is default if not provided` \
    table
