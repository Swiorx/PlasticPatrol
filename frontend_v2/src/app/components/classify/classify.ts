import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClassifierService, ClassifyResult } from '../../services/classifier.service';

@Component({
  selector: 'app-classify',
  imports: [CommonModule],
  templateUrl: './classify.html',
  styleUrl: './classify.scss',
})
export class ClassifyComponent {
  private classifier = inject(ClassifierService);

  dragOver = false;
  loading = false;
  result: ClassifyResult | null = null;
  preview: string | null = null;
  error = '';

  onDragOver(e: DragEvent) { e.preventDefault(); this.dragOver = true; }
  onDragLeave() { this.dragOver = false; }

  onDrop(e: DragEvent) {
    e.preventDefault();
    this.dragOver = false;
    const file = e.dataTransfer?.files[0];
    if (file) this.classify(file);
  }

  onFileSelect(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) this.classify(file);
  }

  private classify(file: File) {
    this.error = '';
    this.result = null;
    const reader = new FileReader();
    reader.onload = () => { this.preview = reader.result as string; };
    reader.readAsDataURL(file);
    this.loading = true;
    this.classifier.classify(file).subscribe({
      next: (r: ClassifyResult) => { this.result = r; this.loading = false; },
      error: () => { this.error = 'Classification failed — is the backend running?'; this.loading = false; }
    });
  }

  reset() { this.result = null; this.preview = null; this.error = ''; }

  get confidencePct() { return this.result ? Math.round(this.result.confidence * 100) : 0; }
}
