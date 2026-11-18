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
