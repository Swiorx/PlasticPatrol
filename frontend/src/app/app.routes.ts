import { Routes } from '@angular/router';
import { Home } from './components/home/home';
import { Map } from './components/map/map';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'map', component: Map },
  { path: '**', redirectTo: '' }
];
