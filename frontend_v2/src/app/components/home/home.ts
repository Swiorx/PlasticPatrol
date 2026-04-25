import { Component, OnInit, OnDestroy, inject, PLATFORM_ID, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';
import { StatsService, StatsResponse } from '../../services/stats.service';

@Component({
  selector: 'app-home',
  imports: [RouterLink, DecimalPipe],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home implements OnInit, AfterViewInit, OnDestroy {
  private statsService = inject(StatsService);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  @ViewChild('waterBg') waterBg!: ElementRef<HTMLElement>;
  @ViewChild('heroText') heroText!: ElementRef<HTMLElement>;
  @ViewChild('scrollHint') scrollHint!: ElementRef<HTMLElement>;

  stats: StatsResponse | null = null;

  ngOnInit() {
    this.statsService.getStats().subscribe({ next: s => this.stats = s, error: () => {} });
  }

  ngAfterViewInit() {
    if (this.isBrowser) {
      window.addEventListener('scroll', this.onScroll, { passive: true });
    }
  }

  private onScroll = () => {
    const y = window.scrollY;

    // water drifts at 40% of scroll speed
    if (this.waterBg?.nativeElement) {
      this.waterBg.nativeElement.style.transform = `translateY(${y * 0.4}px)`;
    }

    // text moves at 65% and fades out
    if (this.heroText?.nativeElement) {
      const opacity = Math.max(0, 1 - y / 380);
      this.heroText.nativeElement.style.transform = `translateY(${y * 0.65}px)`;
      this.heroText.nativeElement.style.opacity = `${opacity}`;
    }

    // scroll hint fades quickly
    if (this.scrollHint?.nativeElement) {
      this.scrollHint.nativeElement.style.opacity = `${Math.max(0, 1 - y / 120)}`;
    }
  };

  ngOnDestroy() {
    if (this.isBrowser) {
      window.removeEventListener('scroll', this.onScroll);
    }
  }
}
