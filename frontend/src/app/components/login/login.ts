import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { Header } from '../header/header';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, Header],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  username = '';
  password = '';
  errorMsg: string | null = null;
  loading = false;

  constructor(
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  submit() {
    this.errorMsg = null;
    this.loading = true;
    this.auth.login(this.username, this.password).subscribe({
      next: () => {
        this.loading = false;
        const target = this.route.snapshot.queryParamMap.get('returnUrl') || '/map';
        this.router.navigateByUrl(target);
      },
      error: (err: HttpErrorResponse) => {
        this.loading = false;
        this.errorMsg = err.error?.detail || 'Login failed';
      },
    });
  }
}
