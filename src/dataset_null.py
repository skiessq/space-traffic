import duckdb
import pandas


def run():
    with duckdb.connect("space_traffic.db") as con:
        summary_df = con.sql("summarize select * from stg_esa_conjunctions").df() 

        null_columns = summary_df[summary_df['null_percentage'] > 0][['column_name', 'null_percentage']]
        print("Columns with null values for stg_esa_conjunctions validation:")
        print(null_columns)

if __name__ == "__main__":
    run()