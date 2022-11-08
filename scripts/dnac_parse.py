with open("mock_data/dnac_maglev_restore_history") as stream:
    s = stream.read()

lines = s.split("\n")
results = [line for line in lines if "RESTORE.FINALIZE_RESTORE" in line]
result = results.pop(-1)
result = result.split()
# ['2022-03-22', '21:23:09', 'ee84abae-a11b-45c6-94c3-d578cfe888f6',
# 'RESTORE.FINALIZE_RESTORE', 'SUCCESS']
print(result[0])
print(result[2])
