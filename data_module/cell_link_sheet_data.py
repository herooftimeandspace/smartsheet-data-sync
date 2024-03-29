import json
import logging
import re

import smartsheet

import data_module.helper as helper
import data_module.smartsheet_api as smartsheet_api
import app.variables as app_vars
import data_module.write_data as write_data


def write_uuid_cell_links(project_data_index, source_sheets):
    """If the description column has a value, look it up against
       the UUIDs in the project dictionary. If a UUID matches, sync
       details.

    Args:
        project_data_index (dict): All UUIDs and the row values
        source_sheets (list): All sheet objects in all workspaces

    Raises:
        TypeError: Project Data Index must be a dict
        ValueError: If the project index data passed in is None,
                    raises and logs an error.
    """
    if not isinstance(project_data_index, dict):
        msg = str("Project data index must be type: dict, not"
                  " {}").format(type(project_data_index))
        log_msg = str("Project index data is None. Aborting the process for "
                      "linking cells by UUID.")
        logging.info(log_msg)
        raise TypeError(msg)
    if not isinstance(source_sheets, list):
        msg = str("Source sheets should be type: list, not {}").format(
            type(source_sheets))
        raise TypeError(msg)

    # dest_uuid = sheet_id, row_id where we create the cell links. Data is
    # pulled INTO this row with the cell link.

    # source_uuid = sheet_id, row_id where the data is coming FROM via
    # the cell link. source_uuid is located in the description column
    # of the uuid:row_data.
    for dest_uuid, row_data in project_data_index.items():
        rows_to_update = []
        sync_columns = None
        result = None
        dest_uuid_col_dict = {}
        source_uuid_col_dict = {}

        if row_data[app_vars.description_col] is None:
            msg = str("Description is {}. No cell link needed. "
                      "Continuing to next UUID"
                      "").format(row_data[app_vars.description_col])
            logging.debug(msg)
            continue
        elif row_data[app_vars.description_col] \
                not in project_data_index.keys():
            msg = str("{} in the description field doesn't match any "
                      "UUID in the index. Continuing to next "
                      "UUID.").format(row_data[app_vars.description_col])
            logging.debug(msg)
            continue
        elif dest_uuid == row_data[app_vars.description_col]:
            msg = str("UUID {} can't link to itself. "
                      "Continuing to next UUID.").format(dest_uuid)
            logging.warning(msg)
            continue
        elif row_data[app_vars.jira_col]:
            msg = str("Row has a Jira ticket value of {}. "
                      "Jira cell links are preferred over UUID links, "
                      "Continuing to next UUID."
                      "").format(row_data[app_vars.jira_col])
            logging.debug(msg)
            continue
        elif row_data[app_vars.predecessor_col] is not None \
                and row_data[app_vars.start_col] is None:
            msg = str("Row has a predecessor value of {} but a start date "
                      "of {}. Continuing to next UUID."
                      "").format(row_data[app_vars.predecessor_col])
            logging.debug(msg)
            continue
        elif row_data[app_vars.predecessor_col] is not None \
                and row_data[app_vars.start_col] is not None:
            msg = str("Checking predecessor(s) for start date {}, "
                      "starting with predecessor row {}"
                      "").format(row_data[app_vars.start_col],
                                 row_data[app_vars.predecessor_col])
            logging.debug(msg)
            result = write_data.write_predecessor_dates(row_data,
                                                        project_data_index)
            if result:
                sync_columns = [app_vars.status_col, app_vars.assignee_col,
                                app_vars.task_col, app_vars.duration_col]
            else:
                sync_columns = [app_vars.status_col, app_vars.assignee_col,
                                app_vars.task_col, app_vars.start_col,
                                app_vars.duration_col]
                result = False
            msg = str("Writing predecessor dates returned {}. Setting "
                      "sync columns to {}.").format(result, sync_columns)
            logging.debug(msg)
        elif row_data[app_vars.predecessor_col] is None:
            sync_columns = [app_vars.status_col, app_vars.assignee_col,
                            app_vars.task_col, app_vars.start_col,
                            app_vars.duration_col]
            msg = str("Row has a predecessor value of {} but a start date "
                      "of {}. Setting sync columns to {}"
                      "").format(row_data[app_vars.predecessor_col],
                                 row_data[app_vars.start_col],
                                 sync_columns)
            logging.debug(msg)
        else:
            msg = str("Unknown error while checking UUID {} "
                      "and values {}").format(dest_uuid, row_data)
            logging.error(msg)
            break

        if result:
            msg = str("Made it through the conditional checks. Values set: "
                      "Sync Columns: {}, "
                      "Predecessor Dates result: {}, "
                      "UUID: {}, "
                      "Row data: {}"
                      "").format(sync_columns, result, dest_uuid, row_data)
        else:
            msg = str("Made it through the conditional checks. Values set: "
                      "Sync Columns: {}, "
                      "Predecessor Dates result: Skipped, "
                      "UUID: {}, "
                      "Row data: {}"
                      "").format(sync_columns, dest_uuid, row_data)
        logging.debug(msg)

        # Make sure that the description matches our UUID pattern
        if bool(re.match(r"\d+-\d+-\d+-\d+",
                         row_data[app_vars.description_col])):
            # Create a cell link from source_uuid -> uuid
            # Pull from this UUID
            source_uuid = row_data[app_vars.description_col]
            dest_sheet = None
            for dest_sheet in source_sheets:
                # Load column names and IDs for the dest_sheet sheet.
                if int(dest_uuid.split("-")[0]) == dest_sheet.id:
                    column_names = helper.json_extract(
                        json.loads(str(dest_sheet)), "title")
                    column_ids = helper.json_extract(
                        json.loads(str(dest_sheet)), "id")
                    dest_uuid_col_dict = dict(zip(column_names, column_ids))
                    dest_sheet = dest_sheet
                    break
                else:
                    msg = str("No match between Destination UUID: {} and "
                              "sheet ID: {}").format(dest_uuid.split("-")[0],
                                                     dest_sheet.id)
                    logging.debug(msg)
                    dest_sheet = None

            msg = "Broke dest_sheet loop. Dict {}".format(
                dest_uuid_col_dict)
            logging.debug(msg)
            if dest_sheet is not None:
                msg = str("Destination Sheet ID: {} | Sheet Name: {} "
                          "set for UUID {}").format(dest_sheet.id,
                                                    dest_sheet.name, dest_uuid)
                logging.error(msg)
            else:
                msg = str("Destination sheet not set for UUID {}. "
                          "Continuing to next UUID.").format(dest_uuid)
                logging.warning(msg)
                continue

            src_sheet = None
            for src_sheet in source_sheets:
                # Load column names and IDs for the src_sheet sheet.
                if int(source_uuid.split("-")[0]) == src_sheet.id:
                    column_names = helper.json_extract(
                        json.loads(str(src_sheet)), "title")
                    column_ids = helper.json_extract(
                        json.loads(str(src_sheet)), "id")
                    source_uuid_col_dict = dict(zip(column_names, column_ids))
                    src_sheet = src_sheet
                    break
                else:
                    msg = str("No match between Source UUID: {} and sheet ID: "
                              "{}").format(source_uuid.split("-")[0],
                                           src_sheet.id)
                    logging.debug(msg)
                    src_sheet = None

            msg = "Broke src_sheet loop. Dict {}".format(
                source_uuid_col_dict)
            logging.debug(msg)
            if src_sheet is not None:
                msg = str("Source Sheet ID: {} | Sheet Name: {} "
                          "set for UUID {}").format(src_sheet.id,
                                                    src_sheet.name,
                                                    source_uuid)
                logging.error(msg)
            else:
                msg = str("Destination sheet not set for UUID {}. "
                          "Continuing to next UUID.").format(source_uuid)
                logging.warning(msg)
                continue

            new_row = smartsheet.models.Row()
            new_row.id = int(dest_uuid.split("-")[1])
            dest_col_map = helper.get_column_map(dest_sheet)
            dest_row = None
            for row in dest_sheet.rows:
                if row.id == new_row.id:
                    dest_row = row
                    msg = str("Destination Row ID {} matched Row ID {} "
                              "in Destination Sheet ID: {} | Sheet Name: {}."
                              "").format(
                        new_row.id, row.id, dest_sheet.id,
                        dest_sheet.name)
                    logging.debug(msg)
                else:
                    msg = str("Destination Row ID {} does not match Row ID {} "
                              "in Destination Sheet ID: {} | Sheet Name: {}. "
                              "Continuing to next row.").format(
                        new_row.id, row.id, dest_sheet.id,
                        dest_sheet.name)
                    logging.debug(msg)
            else:
                logging.debug(dest_row)
                if dest_row is not None:
                    desc_cell = helper.get_cell_data(
                        dest_row, app_vars.description_col, dest_col_map)
                    logging.debug(desc_cell.value)

            for col in sync_columns:
                if dest_row:
                    cell = helper.get_cell_data(row, col, dest_col_map)
                    link_status = helper.has_cell_link(cell, 'In')
                    link_out_status = helper.has_cell_link(cell, 'Out')
                    msg = str("{}, {}").format(cell, link_status)
                    logging.debug(msg)
                else:
                    msg = str("Destination row data not found. Breaking loop.")
                    logging.debug(msg)
                    break

                if link_status in ("OK", "Linked"):
                    msg = str("Destination cell value {} has a valid cell "
                              "link: {}. Continuing to next cell.").format(
                        cell.value, cell.link_in_from_cell)
                    logging.debug(msg)
                    continue
                elif link_status is None:
                    msg = str("Destination cell value {} is not a valid "
                              "cell link value. Continuing to next cell."
                              "").format(cell.value)
                    logging.debug(msg)
                    continue
                elif link_status in ("Unlinked", "BROKEN", "Broken"):
                    if desc_cell:
                        msg = str("Cell link status is {}. "
                                  "Writing new cell link."
                                  "").format(link_status)
                        logging.debug(msg)
                    else:
                        msg = str("Cell link status is {} but Description"
                                  "field is {}. Continuing to next cell."
                                  "").format(link_status, desc_cell)
                        logging.debug(msg)
                        continue
                else:
                    msg = str("Cell link status is {}. "
                              "Sheet ID: {} | Row ID: {} "
                              "| Column: {} | Cell Details: {}"
                              "").format(link_status, dest_sheet.id,
                                         row.id, col, cell)
                    logging.warning(msg)

                # If the column in our list of columns to sync is a
                # key in the destination uuid column dictionary,
                # return the destination column ID.
                if col in dest_uuid_col_dict.keys():
                    dest_col_id = dest_uuid_col_dict[col]

                # If the column in our list of columns to sync is a
                # key in the source uuid column dictionary,
                # return the source column ID.
                source_col_id = None
                if col in source_uuid_col_dict.keys():
                    source_col_id = source_uuid_col_dict[col]

                if not source_col_id:
                    logging.debug(
                        "Source column ID is empty. "
                        "Continuing to next column.")
                    continue
                elif not dest_col_id:
                    logging.debug(
                        "Destination column ID is empty. "
                        "Continuing to next column.")
                    continue
                else:
                    # Cell Link object the data coming from source_uuid.
                    cell_link = smartsheet.models.CellLink()
                    cell_link.sheet_id = int(source_uuid.split("-")[0])
                    cell_link.row_id = int(source_uuid.split("-")[1])
                    cell_link.column_id = int(source_col_id)

                    # New Cell object is written to the dest_uuid sheet.
                    new_cell = smartsheet.models.Cell()
                    new_cell.column_id = int(dest_col_id)
                    new_cell.value = smartsheet.models.ExplicitNull()
                    new_cell.link_in_from_cell = cell_link

                    # Append the new cell to the row after all the parameters
                    # have been set.
                    new_row.cells.append(new_cell)
            if new_row.cells:
                # Append the new row to the list of rows to update
                rows_to_update.append(new_row)

                # TODO: Figure out why rows with outgoing links are written.
                msg = str("{}, {}").format(new_row, link_out_status)
                logging.error(msg)
            else:
                msg = str("Destination UUID {} has valid linked "
                          "cells. No update needed. Continuing to next UUID."
                          "").format(dest_uuid)
                logging.debug(msg)
                continue
        else:
            logging.debug("Error matching the UUID pattern to"
                          "the value in the description field.")
            logging.debug(dest_uuid, row_data)

        # Write back all rows after parsing through the list of UUIDs
        if rows_to_update:
            msg = str("Writing {} cell link row(s) back to Sheet ID: {} "
                      "| Sheet Name: {}").format(len(rows_to_update),
                                                 dest_sheet.id,
                                                 dest_sheet.name)
            logging.info(msg)
            smartsheet_api.write_rows_to_sheet(rows_to_update, dest_sheet,
                                               write_method="update")
        else:
            logging.debug("No updates required.")
