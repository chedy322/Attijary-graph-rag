export interface AuditLog {
  id: string;
  action: string;
  target_resource: string;
  ip_address: string;
  details: string;
  created_at: string;
}
