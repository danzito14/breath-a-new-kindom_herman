import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface maxandmin {
  min_price: number;
  max_price: number;
}

@Injectable({
  providedIn: 'root'
})
export class MaxAndMinPrice {
  private apiUrl = 'http://127.0.0.1:8000/home/get_max_and_min_price';

  constructor(private http: HttpClient) { }

  get_min_and_max_price(): Observable<maxandmin> {
    return this.http.get<maxandmin>(this.apiUrl);
  }
}
