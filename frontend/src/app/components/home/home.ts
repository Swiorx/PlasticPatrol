import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Header } from '../header/header';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, Header],
  templateUrl: './home.html',
  styleUrl: './home.scss'
})
export class Home {}
