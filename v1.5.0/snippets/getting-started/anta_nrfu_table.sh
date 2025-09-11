anta nrfu \
    --username arista \
    --password arista \
    --inventory ./inventory.yml \
    `# uncomment the next two lines if you have an enable password `\
    `# --enable` \
    `# --enable-password <password>` \
    --catalog ./catalog.yml \
    `# table is default if not provided` \
    table
