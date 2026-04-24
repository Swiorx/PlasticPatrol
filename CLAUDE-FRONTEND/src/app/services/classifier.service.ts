import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface ClassifyResult {
  label: 'clean' | 'debris';
  confidence: number;
}

@Injectable({ providedIn: 'root' })
export class ClassifierService {
  constructor(private http: HttpClient) {}

  classify(file: File) {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<ClassifyResult>('http://localhost:8000/api/classify', form);
  }
}
