path "nomos/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "nomos/metadata/*" {
  capabilities = ["read", "list"]
}
