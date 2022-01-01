async def local_remote_compare(local, remote, check):
    added = remote
    persistent = []
    removed = []
    for l in local:
        found = False
        for i, r in enumerate(added):
            # Item found
            if check(l, r):
                found = True
                break
        # Local not found in remote, remove
        if not found:
            removed.append(l)
        # Else, append to unmodified, and remove from list
        else:
            persistent.append((l, r))
            del added[i]
    # Remaining items have been added
    return added, removed, persistent
