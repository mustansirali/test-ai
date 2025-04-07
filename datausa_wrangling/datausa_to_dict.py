import pandas as pd

csv_col_map = {
    'Citizenship':['Citizenship %'],
    'Race and Ethnicity':{
        'Race':'share'
    },
    'Applicants, Admissions &amp; Enrolled':['Admissions Enrolled', 'Admissions','Admitted who Enrolled','Applicant Admitted','Applicants'],
    'Property':{
        'Value Bucket':'share'
    },
    'Occupations':{
        'Occupation':'Share'
    },
    'Uninsured People':{
        'Kaiser Coverage':'share'
    },
    'Rent vs Own':['share'],
    'Employment by Industries':{
        'Industry':'Share'
    },
    'Household Income':{
        'Household Income Bucket':'share'
    }
}
percent_set = set(['Property','Household Income'])

def reduce(csv_path: str,geo_id:str) -> pd.DataFrame:
    df = pd.read_csv(f"../austin_raw/{csv_path}")
    df = df[df['ID Geography'] == geo_id]
    df = df.drop(columns=['ID Geography'])
    latest_year = df['Year'].max()
    df = df[df['Year'] == latest_year]
    return df,latest_year

def csvs_to_dict(csv_paths:list,geo_id:str)->dict:
    geo_data = {}
    for csv in csv_paths:
        if csv.endswith('.csv') and csv[:-4] in csv_col_map:
            var_name = csv[:-4]
            df,year = reduce(csv,geo_id)
            col_map = csv_col_map[var_name]
            geo_data[var_name] = {}
            geo_data[var_name]['year'] = int(year)
            if isinstance(col_map,list):
                for var in col_map:
                    geo_data[var_name][var] = float(df[var].sum())
            else:
                for key_col,val_col in col_map.items():
                    for key_col_group in df[key_col].unique():
                        try:
                            geo_data[var_name][key_col_group] = float(df[df[key_col] == key_col_group][val_col].sum())
                        except KeyError:
                            print(csv)
            if var_name in percent_set:
                for k,v in geo_data[var_name].items():
                    if k != 'year':
                        geo_data[var_name][k] = v*100
            

    return geo_data 