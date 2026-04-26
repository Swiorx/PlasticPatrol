import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
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
  reservationsError: string | null = null;

  constructor(
    public auth: AuthService, 
    private api: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef
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
    this.reservationsError = null;
    this.api.getReservations().subscribe({
      next: (res) => {
        this.reservations = res;
        this.loadingReservations = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading reservations:', err);
        this.reservationsError = 'Eroare la încărcarea rezervărilor. Repornește scriptul de backend!';
        this.loadingReservations = false;
        this.cdr.detectChanges();
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
