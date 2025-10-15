import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TarjetaOferta } from './tarjeta-oferta';

describe('TarjetaOferta', () => {
  let component: TarjetaOferta;
  let fixture: ComponentFixture<TarjetaOferta>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TarjetaOferta]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TarjetaOferta);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
