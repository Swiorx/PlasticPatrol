import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class RegisterComponent {
  private auth = inject(AuthService);
  private router = inject(Router);

  username = '';
  email = '';
  password = '';
  loading = false;
  error = '';

  submit() {
    this.error = '';
    this.loading = true;
    this.auth.register(this.username, this.email, this.password).subscribe({
      next: () => this.router.navigate(['/login']),
      error: (e: any) => {
        this.error = e.error?.detail ?? 'Registration failed. Try again.';
        this.loading = false;
      }
    });
  }
}
