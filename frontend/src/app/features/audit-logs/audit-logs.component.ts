import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuditService } from '../../core/services/audit.service';
import { AuditLog } from '../../core/models/audit-log.model';

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-logs.component.html',
  styleUrl: './audit-logs.component.scss',
})
export class AuditLogsComponent implements OnInit {
  private auditService = inject(AuditService);

  logs: AuditLog[] = [];
  filteredLogs: AuditLog[] = [];
  isLoading = false;
  errorMessage: string | null = null;
  searchTerm = '';
  selectedAction = 'ALL';
  selectedResource = 'ALL';
  selectedRange = 'ALL';
  currentPage = 1;
  pageSize = 10;
  totalLogs = 0;
  totalPages = 0;

  ngOnInit(): void {
    this.loadLogs();
  }

  get actions(): string[] {
    return this.uniqueValues('action');
  }

  get resources(): string[] {
    return this.uniqueValues('target_resource');
  }

  get pageStart(): number {
    return this.logs.length ? (this.currentPage - 1) * this.pageSize + 1 : 0;
  }

  get pageEnd(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalLogs);
  }

  loadLogs(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.auditService.getLogs(this.currentPage, this.pageSize).subscribe({
      next: (response) => {
        this.logs = Array.isArray(response.data) ? response.data : [];
        this.totalLogs = response.meta?.total ?? 0;
        this.totalPages = response.meta?.total_pages ?? 0;
        this.applyFilters();
        this.isLoading = false;
      },
      error: (error) => {
        this.logs = [];
        this.filteredLogs = [];
        this.totalLogs = 0;
        this.totalPages = 0;
        this.isLoading = false;
        this.errorMessage = error?.error?.message || error?.message || 'Unable to load audit logs.';
      },
    });
  }

  applyFilters(): void {
    const query = this.searchTerm.trim().toLowerCase();
    this.filteredLogs = this.logs.filter((log) => {
      const matchesSearch = !query || [log.action, log.target_resource, log.ip_address, log.details]
        .some((value) => value?.toLowerCase().includes(query));
      const matchesAction = this.selectedAction === 'ALL' || log.action === this.selectedAction;
      const matchesResource = this.selectedResource === 'ALL' || log.target_resource === this.selectedResource;
      const matchesRange = this.matchesRange(log.created_at);
      return matchesSearch && matchesAction && matchesResource && matchesRange;
    });
  }

  setPage(page: number): void {
    if (page < 1 || page === this.currentPage || (page > this.currentPage && (this.totalPages === 0 || page > this.totalPages))) return;
    this.currentPage = page;
    this.loadLogs();
  }

  exportLogs(): void {
    const rows = this.filteredLogs.map((log) => [
      log.created_at, log.action, log.target_resource, log.ip_address, log.details,
    ].map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`).join(','));
    const csv = ['Time,Action,Target Resource,IP Address,Details', ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-logs-page-${this.currentPage}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  actionClass(action: string): string {
    return action.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  }

  resourceIcon(resource: string): string {
    const value = resource.toLowerCase();
    if (value.includes('graph')) return 'network';
    if (value.includes('document')) return 'file';
    if (value.includes('setting')) return 'gear';
    if (value.includes('platform')) return 'shield';
    if (value.includes('audit')) return 'download';
    return 'eye';
  }

  trackById(_: number, log: AuditLog): string { return log.id; }

  private uniqueValues(key: 'action' | 'target_resource'): string[] {
    return [...new Set(this.logs.map((log) => log[key]).filter(Boolean))].sort();
  }

  private matchesRange(createdAt: string): boolean {
    if (this.selectedRange === 'ALL') return true;
    const timestamp = new Date(createdAt).getTime();
    const days = Number(this.selectedRange);
    return timestamp >= Date.now() - days * 24 * 60 * 60 * 1000;
  }
}
