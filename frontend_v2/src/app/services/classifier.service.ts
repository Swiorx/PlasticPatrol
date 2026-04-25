import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from './auth.service';

export interface ClassifyResult {
  label: 'debris' | 'clean';
  confidence: number;
}

@Injectable({ providedIn: 'root' })
export class ClassifierService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  classify(file: File) {
    const form = new FormData();
    form.append('file', file);
    const token = this.auth.getToken();
    const headers = token ? new HttpHeaders({ Authorization: `Bearer ${token}` }) : undefined;
    return this.http.post<ClassifyResult>('http://localhost:8000/api/classify', form, { headers });
  }
}
