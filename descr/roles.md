# Role Maintenance – civilistes, doctorants, directeurs, assistants

## Civilistes: exact editorial role

`sync_status_roles --apply` creates the `civilistes` group when needed and
reconciles it to an exact least-privilege policy. Unlike the older status
groups, permissions outside this allow-list are removed from this group:

- view, add and edit bibliographies and transcriptions, including records
  assigned by another researcher;
- access unpublished transcriptions for pagination, IIIF and tagging work;
- use existing person and place authorities in tagging;
- view, add and edit document attachments, including an assigned attachment;
- delete only bibliographies, transcriptions and attachments owned by the
  civiliste (the application enforces ownership).

The role deliberately excludes publication, ownership transfer, deletion of
third-party content, confidential-note oversight, person/place creation from
tagging, user/group administration and Django admin access. A Civiliste account
must remain `is_staff=False` and must not also belong to `directeurs` or another
broader group. Account reassignment is a separate, explicitly reviewed
operation; the synchronization command never changes group memberships.

Before staging, preview the reconciliation and review both the grants and the
revocations:

```bash
python app/manage.py sync_status_roles
python app/manage.py sync_status_roles --apply
python app/manage.py sync_status_roles
```

The final dry-run must report that `civilistes` already matches the exact
policy and that no Civiliste account has conflicting elevated access. A warning
lists accounts that are also in `directeurs`, have `is_staff=True`, or have
`is_superuser=True`; the command reports these conflicts but deliberately does
not change memberships. Resolve every warning before staging. Then validate
with a dedicated non-staff Civiliste account: editing a third-party draft,
existing-authority tagging, pagination/IIIF, attachment creation/editing,
refusal of inline authority creation, refusal of publication, and refusal to
delete third-party content.

## Removing/Reassigning the legacy "assistants" role
1. **List current members**
   ```bash
   docker compose -f docker/docker-compose.staging.yml exec web \
     bash -lc "python /app/app/manage.py shell -c 'from django.contrib.auth.models import User, Group; g=Group.objects.get(name=\"assistants\"); print(list(g.user_set.values_list(\"username\", flat=True)))'"
   ```
2. **Reassign users as needed** (via admin or shell) – e.g. move to `doctorants`/`chercheurs` or deactivate test accounts.
3. **Preview changes**
   ```bash
   docker compose -f docker/docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles'
   ```
   Confirm the assistant group is empty (`X associated user(s)` shown). If not, loop back to step 2.
4. **Apply changes**
   ```bash
   docker compose -f docker/docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles --apply'
   ```
   This creates `fiches.change_collection_owner` (if missing), grants it to “directeurs”, and deletes the assistant group.
5. **Verify**
   ```bash
   docker compose -f docker/docker-compose.staging.yml exec web \
     bash -lc 'python /app/app/manage.py sync_status_roles'
   ```
   Output should show: permission exists, directeurs already hold it, no assistant group found.

## Adding/Checking the custom permissions
- The same `sync_status_roles` command also ensures doctorants receive document attachment permissions (`add/change/delete_documentfile`).
- It also ensures doctorants can access and edit third-party transcriptions (`access_unpublished_transcription`, `change_any_transcription`).
- It exactly reconciles the `civilistes` group; review revocations before using
  `--apply` in any shared environment.
- Run the command after an exceptional DB restore, auth-table refresh, or environment rebuild so groups stay aligned.

## Allowing staff to manage user profiles
Some staff accounts (e.g., those who create new users) must see and edit the “Informations supplémentaires” inline in the Django admin. After an exceptional database restore or auth-table overwrite:

1. Open the user in **Django admin → Utilisateurs**.
2. In the **Permissions** section grant:
   - `auth | user | Can add user`
   - `auth | user | Can change user`
   - `fiches | Informations supplémentaires | Can add user profile`
   - `fiches | Informations supplémentaires | Can change user profile`
   - `fiches | Informations supplémentaires | Can delete user profile`
   - `fiches | Informations supplémentaires | Can view informations supplémentaires`
3. Save the user; the “Domaine de recherche / Historique” field reappears for that account.

Repeat these assignments any time a restore overwrites the auth tables, otherwise the inline disappears for non-superusers.
