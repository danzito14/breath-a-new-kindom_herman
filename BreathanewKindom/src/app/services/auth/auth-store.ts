import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthStoreService {
  private tokenSubject = new BehaviorSubject<string | null>(null);
  token$ = this.tokenSubject.asObservable();

  constructor() {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      this.tokenSubject.next(token);
    }
  }

  setToken(token: string) {
    if (typeof window !== 'undefined') localStorage.setItem('token', token);
    this.tokenSubject.next(token);
  }

  clearToken() {
    if (typeof window !== 'undefined') localStorage.removeItem('token');
    this.tokenSubject.next(null);
  }

  getToken(): string | null {
    return this.tokenSubject.value;
  }
}
