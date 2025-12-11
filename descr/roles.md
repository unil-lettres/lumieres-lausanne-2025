# Role Maintenance – doctorants, directeurs, assistants

## Removing/Reassigning the legacy "assistants" role
1. **List current members**
   ```bash
   docker compose -f docker-compose.staging.yml exec web \
     bash -lc "python /app/app/manage.py shell -c 'from django.contrib.auth.models import User, Group; g=Group.objects.get(name=\"assistants\"); print(list(g.user_set.values_list(\"username\", flat=True)))'"
   ```
2. **Reassign users as needed** (via admin or shell) – e.g. move to `doctorants`/`chercheurs` or deactivate test accounts.
3. **Preview changes**
   ```bash
   docker compose -f docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles'
   ```
   Confirm the assistant group is empty (`X associated user(s)` shown). If not, loop back to step 2.
4. **Apply changes**
   ```bash
   docker compose -f docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles --apply'
   ```
   This creates `fiches.change_collection_owner` (if missing), grants it to “directeurs”, and deletes the assistant group.
5. **Verify**
   ```bash
   docker compose -f docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles'
   ```
   Output should show: permission exists, directeurs already hold it, no assistant group found.

## Adding/Checking the custom permissions
- The same `sync_status_roles` command also ensures doctorants receive document attachment permissions (`add/change/delete_documentfile`).
- Run the command after importing a database dump from production so groups stay aligned.

## Allowing staff to manage user profiles
Some staff accounts (e.g., those who create new users) must see and edit the “Informations supplémentaires” inline in the Django admin. After each database refresh from production:

1. Open the user in **Django admin → Utilisateurs**.
2. In the **Permissions** section grant:
   - `auth | user | Can add user`
   - `auth | user | Can change user`
   - `fiches | Informations supplémentaires | Can add user profile`
   - `fiches | Informations supplémentaires | Can change user profile`
   - `fiches | Informations supplémentaires | Can delete user profile`
   - `fiches | Informations supplémentaires | Can view informations supplémentaires`
3. Save the user; the “Domaine de recherche / Historique” field reappears for that account.

Repeat these assignments any time a fresh production dump overwrites the auth tables, otherwise the inline disappears for non-superusers.
