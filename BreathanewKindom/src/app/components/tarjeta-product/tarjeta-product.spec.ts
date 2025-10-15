import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TarjetaProduct } from './tarjeta-product';

describe('TarjetaProduct', () => {
  let component: TarjetaProduct;
  let fixture: ComponentFixture<TarjetaProduct>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TarjetaProduct]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TarjetaProduct);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
