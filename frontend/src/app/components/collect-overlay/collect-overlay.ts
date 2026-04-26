import { Component, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService } from '../../services/api.service';

type OverlayState = 'idle' | 'loading' | 'fail' | 'released' | 'success';

@Component({
  selector: 'app-collect-overlay',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './collect-overlay.html',
})
export class CollectOverlayComponent {
  @Input() reservationId!: number;
  @Input() ecoPoints!: number;
  @Output() closed = new EventEmitter<void>();
  @Output() collected = new EventEmitter<void>();

  state: OverlayState = 'idle';
  message = '';
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    this.selectedFile = input.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      this.previewUrl = e.target?.result as string;
      this.cdr.detectChanges();
    };
    reader.readAsDataURL(this.selectedFile);
  }

  submit() {
    if (!this.selectedFile || this.state === 'loading') return;
    this.state = 'loading';
    this.cdr.detectChanges();

    this.api.collectCluster(this.reservationId, this.selectedFile).subscribe({
      next: (res) => {
        this.state = 'success';
        this.message = res.message;
        this.cdr.detectChanges();
        setTimeout(() => this.collected.emit(), 1800);
      },
      error: (err: HttpErrorResponse) => {
        const detail: string = err.error?.detail || 'Verification failed. Please retry.';
        if (detail.includes('released') || detail.includes('3 attempt')) {
          this.state = 'released';
          this.message = detail;
          this.cdr.detectChanges();
          setTimeout(() => this.closed.emit(), 2500);
        } else {
          this.state = 'fail';
          this.message = detail;
          this.selectedFile = null;
          this.previewUrl = null;
          this.cdr.detectChanges();
        }
      }
    });
  }

  get isLoading(): boolean {
    return this.state === 'loading';
  }

  cancel() {
    this.closed.emit();
  }
}
