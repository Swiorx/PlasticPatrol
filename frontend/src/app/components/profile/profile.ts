import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Header } from '../header/header';
import { AuthService, UserOut } from '../../services/auth.service';
import { ApiService, ReservationOut } from '../../services/api.service';
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
  reservations: ReservationOut[] = [];
  loadingReservations = false;

  constructor(
    public auth: AuthService, 
    private api: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.user = this.auth.currentUser();
    if (!this.user) {
      this.router.navigateByUrl('/login');
    } else {
      this.loadReservations();
    }
  }

  loadReservations() {
    this.loadingReservations = true;
    this.api.getReservations().subscribe({
      next: (res) => {
        this.reservations = res;
        this.loadingReservations = false;
      },
      error: () => {
        this.loadingReservations = false;
      }
    });
  }

  cancelReservation(id: number) {
    if (!confirm('Are you sure you want to cancel this reservation?')) return;
    
    this.api.releaseReservation(id).subscribe({
      next: () => {
        this.loadReservations();
      },
      error: (err) => {
        console.error('Failed to cancel reservation', err);
        alert('Failed to cancel reservation');
      }
    });
  }

  logout() {
    this.auth.logout();
    this.router.navigateByUrl('/');
  }
}
