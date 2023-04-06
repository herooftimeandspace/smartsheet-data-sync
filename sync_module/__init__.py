"""The Sync module is responsible for driving synchronization between
            various systems. At present it creates a bidirectional sync
            between each sheet with a Jira Ticket column and the Jira Index
            Sheet (Dev, Staging or Prod depending). If data has changed on
            any two compared sheets, it updates both sheets with the most
            recent data for each cell. This prevents data collisions between
            sheets. The same Jira Ticket can be added to any number of rows,
            and will synchronize with the Index Sheet on every run.
    """
