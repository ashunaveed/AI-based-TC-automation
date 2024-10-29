

def overall_restrictions(df):
    '''
    If there are any rate restrictions, it returns the concatenated sentences containing the restrictions.
    If there is no mention of restrictions, it returns 0.
    
    Parameters:
    df (DataFrame): Input DataFrame to check for restrictions.
    
    Returns:
    str or int: Concatenated string of sentences with restrictions or 0 if no restrictions found.
    '''
    # Convert all entries to strings
    df = df.applymap(str)
    
    # Define strings to check for
    strings_to_check = ['rate', 'restricted', 'future', 'reference', 'banned', 'higher', 'restriction', 'special case']
    
    # Initialize a list to collect matching rows
    final_list = []
    
    # Check for any matching strings in the DataFrame
    mask = df.apply(lambda col: col.str.contains('|'.join(strings_to_check), case=False, na=False))
    
    # Extract the rows where any column contains the strings
    matching_rows = df[mask.any(axis=1)]
    
    if matching_rows.empty:
        return 0
    
    # Concatenate the rows into a single string
    final_list = '\n'.join(matching_rows.apply(lambda row: ' '.join(row), axis=1))
    
    return final_list

def item_restriction(item, schedule, any_restriction, comparer, use_AI):
    '''
    It will return True or False

    '''
    return False



    return restrictions
