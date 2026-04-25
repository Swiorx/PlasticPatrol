import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class Register {
  username = '';
  email = '';
  password = '';
  confirmPassword = '';
  errorMsg: string | null = null;
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  submit() {
    this.errorMsg = null;

    if (this.password.length < 8) {
      this.errorMsg = 'Password must be at least 8 characters';
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.errorMsg = 'Passwords do not match';
      return;
    }

    this.loading = true;
    this.auth.register(this.username, this.email, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigateByUrl('/map');
      },
      error: (err: HttpErrorResponse) => {
        this.loading = false;
        const detail = err.error?.detail;
        if (Array.isArray(detail)) {
          this.errorMsg = detail.map((d: any) => d.msg).join(', ');
        } else {
          this.errorMsg = detail || 'Registration failed';
        }
      },
    });
  }
}
