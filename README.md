# k8s-ollama

Suncoast Systems Kubernetes Ollama and OpenWebUI setup.

## Application access

The shared OpenWebUI authentication bridge authorizes applications through the
comma-separated `ALLOWED_MEMBERSHIP_ROLES` value in
`manifests/15-openwebui-auth-bridge.yaml`. Each entry is a normalized
`suncoast_roles` value produced from Google Groups by Keycloak.

For example:

```yaml
- name: ALLOWED_MEMBERSHIP_ROLES
  value: "research_application_users,another_application_users"
```

An authenticated user must belong to at least one listed group. An empty list
denies access. Application-specific APIs should still enforce their own group;
this list controls only access to the shared Ollama/OpenWebUI service and its
configured models.

## Durable OpenWebUI PostgreSQL target

`manifests/21-openwebui-postgres-target.yaml` manages OpenWebUI's isolated
database on the shared Oracle Cloud PostgreSQL server, a redundant in-cluster
SSH tunnel, and the Vault-backed runtime connection Secret. The target identity
is:

- database: `openwebui`
- schema: `openwebui`
- application role: `openwebui_app`

The bootstrap creates the role, database, and schema only when they are absent.
When the database already exists, it validates the expected database and schema
owners and skips database and schema creation. An ownership mismatch fails the
bootstrap instead of adopting or rebuilding unknown data. The bootstrap also
restricts database connections to `openwebui_app` and checks that the Directus
database identity is unchanged.

Rebuild-critical values follow the Google Secret Manager synchronization
contract: each value exists in Vault at `secret/<secret-name>` under the single
`value` property. Required secret names are:

- `openwebui-db-password`
- `directus_db_ssh_tunnel_host`
- `directus_db_ssh_private_key_b64`

The generated `openwebui-db-url` Secret points OpenWebUI, its authentication
bridge, and database reconciliation Jobs to the internal
`openwebui-postgres.ollama.svc.cluster.local` tunnel Service. OpenWebUI's NFS
model and cache volumes remain on the Kubernetes platform.
