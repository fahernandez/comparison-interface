"""Initialize Flask website database"""
# Custom libraries
from model.connection import db
from model.schema import (Group, Item, CustomItemPair, ItemGroup,
                          UserGroup, Comparison, UserItem)
import pandas as pd
from sqlalchemy import MetaData
from migrate.versioning.schema import Table
from sqlalchemy import text
from sqlalchemy.sql import select
import os


class Export:
    def __init__(self, app) -> None:
        self.app = app
        self.models = [
            Group,
            Item,
            ItemGroup,
            UserGroup,
            Comparison,
            CustomItemPair,
            UserItem
        ]

    def save(self, location):
        """Export the database content into a particular location. The file will be
        save as excel file.

        Args:
            location (string): File location where to save the exported information
        """
        with pd.ExcelWriter(location, mode="w", engine='xlsxwriter') as writer:
            for m in self.models:
                data = m.query.all()
                data_list = [item.as_dict() for item in data]
                df = pd.DataFrame(data_list)
                df.to_excel(writer,m.__tablename__,index=False)
        
            # The user model needs to be accessed manually due the dynamics fields
            db_engine = db.get_engine()
            db_meta = MetaData(bind=db_engine)
            MetaData.reflect(db_meta)
            table = Table('user' , db_meta)
            columns = table.columns.keys()
            
            # Get all columns from the table
            sql = text("select {} from user;".format(', '.join(columns)))
            results = db_engine.execute(sql)
            df = pd.DataFrame(columns=columns)
            for record in results:
                row = pd.DataFrame([dict(record)])
                df = pd.concat([df, row], ignore_index=True)

            # Write the user results
            df.to_excel(writer,'user',index=False)
