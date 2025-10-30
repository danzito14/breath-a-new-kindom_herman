import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MeseroIncio } from './mesero-incio';

describe('MeseroIncio', () => {
  let component: MeseroIncio;
  let fixture: ComponentFixture<MeseroIncio>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MeseroIncio]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MeseroIncio);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
