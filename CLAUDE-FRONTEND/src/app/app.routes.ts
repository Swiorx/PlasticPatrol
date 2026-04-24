import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./components/home/home').then(m => m.Home) },
  { path: 'map', loadComponent: () => import('./components/map/map').then(m => m.MapComponent) },
  { path: 'classify', loadComponent: () => import('./components/classify/classify').then(m => m.ClassifyComponent) },
  { path: 'login', loadComponent: () => import('./components/login/login').then(m => m.LoginComponent) },
  { path: 'register', loadComponent: () => import('./components/register/register').then(m => m.RegisterComponent) },
  { path: '**', redirectTo: '' },
];
