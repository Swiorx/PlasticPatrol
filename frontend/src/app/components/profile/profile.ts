import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Header } from '../header/header';
import { AuthService, UserOut } from '../../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, Header],
  templateUrl: './profile.html',
  styleUrl: './profile.scss'
})
export class Profile implements OnInit {
  user: UserOut | null = null;

  constructor(public auth: AuthService, private router: Router) {}

  ngOnInit() {
    this.user = this.auth.currentUser();
    if (!this.user) {
      this.router.navigateByUrl('/login');
    }
  }

  logout() {
    this.auth.logout();
    this.router.navigateByUrl('/');
  }
}
