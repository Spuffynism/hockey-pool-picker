
# TODO(nico): Find a better name for this method, and file
def merge(dataframes):
    """
    Merges dataframes on index and drops duplicate columns.
    :return:
    """
    assert len(dataframes) >= 2

    merged = dataframes[0]
    for df in dataframes[1:]:
        merged = merged.merge(df, left_index=True, right_index=True,
                              how='left', suffixes=('', '_y'))
        merged.drop(merged.filter(regex='_y$').columns, axis=1, inplace=True)
    return merged