import { TestBed } from '@angular/core/testing';

import { MaxAndMinPrice } from './max-and-min-price';

describe('MaxAndMinPrice', () => {
  let service: MaxAndMinPrice;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MaxAndMinPrice);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
