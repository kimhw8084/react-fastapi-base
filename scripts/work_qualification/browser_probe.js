/*
 * Paste into DevTools on the deployed frontend while signed in as the selected
 * real user. It downloads only allowlisted, hashed observations. Browser
 * credentials are sent by fetch; cookie and header values are never read.
 * bootstrap.csrf_token remains in memory only and is never emitted or stored.
 */
(async () => {
  const fail = () => { console.error('Work qualification probe could not produce a safe observation. Check the deployed session and try again.'); };
  const label = prompt('Observation label: A1, B1, A2, B2, A3, or B3');
  if (!['A1', 'B1', 'A2', 'B2', 'A3', 'B3'].includes(label)) return fail();
  const runtimeResponse = await fetch('/runtime-config.json', { cache: 'no-store', credentials: 'same-origin', redirect: 'error' }).catch(() => null);
  if (!runtimeResponse || !runtimeResponse.ok) return fail();
  const runtime = await runtimeResponse.json().catch(() => null);
  if (!runtime || runtime.schemaVersion !== 1 || typeof runtime.apiBase !== 'string') return fail();
  let api;
  try { api = new URL(runtime.apiBase); } catch { return fail(); }
  if (!['https:', 'http:'].includes(api.protocol) || api.username || api.password || api.pathname !== '/' || api.search || api.hash) return fail();
  const apiBase = api.origin;
  const [bootstrapResponse, proofResponse] = await Promise.all([
    fetch(`${apiBase}/api/v1/bootstrap`, { cache: 'no-store', credentials: 'include', redirect: 'error' }).catch(() => null),
    fetch(`${apiBase}/api/v1/identity-proof`, { cache: 'no-store', credentials: 'include', redirect: 'error' }).catch(() => null),
  ]);
  if (!bootstrapResponse?.ok || !proofResponse?.ok) return fail();
  const bootstrap = await bootstrapResponse.json().catch(() => null);
  const proof = await proofResponse.json().catch(() => null);
  if (!bootstrap || !proof || typeof bootstrap.user_id !== 'string' || typeof proof.instance_id !== 'string' || typeof proof.deployment_id !== 'string') return fail();
  const tenants = Array.isArray(bootstrap.tenants) ? bootstrap.tenants : [];
  if (!tenants.length) return fail();
  const choices = tenants.map((tenant, index) => `${index + 1}. ${String(tenant.name ?? 'Tenant')}`).join('\n');
  const choice = Number(prompt(`Select the dedicated qualification tenant for this observation:\n${choices}`));
  const tenant = tenants[choice - 1];
  if (!tenant || typeof tenant.id !== 'string' || !['admin', 'editor', 'viewer'].includes(tenant.role)) return fail();
  const hash = async value => {
    const bytes = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
  };
  const permissions = Array.isArray(tenant.permissions) ? tenant.permissions.filter(value => ['admin', 'read', 'write', 'comment', 'configure', 'delete', 'export', 'import', 'restore', 'views.personal', 'views.team'].includes(value)).sort() : [];
  const result = {
    schema_version: 1,
    label,
    captured_at: new Date().toISOString(),
    frontend_origin_hash: await hash(location.origin),
    api_base_hash: await hash(apiBase),
    http: { runtime_config: runtimeResponse.status, bootstrap: bootstrapResponse.status, identity_proof: proofResponse.status },
    user_hash: await hash(bootstrap.user_id),
    instance_hash: await hash(proof.instance_id),
    deployment_hash: await hash(proof.deployment_id),
    profile: String(proof.profile),
    identity_source: String(proof.identity_source),
    build_version: String(bootstrap.build_version),
    api_major: Number(bootstrap.api_major),
    api_revision: Number(bootstrap.api_revision),
    tenant_hash: await hash(tenant.id),
    role: tenant.role,
    permissions,
  };
  const blob = new Blob([JSON.stringify(result, null, 2) + '\n'], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `identity-${label}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  console.info(`Saved safe work qualification observation ${label}. The observation contains hashes and allowlisted status fields only.`);
})();
