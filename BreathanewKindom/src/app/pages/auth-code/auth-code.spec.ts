import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthCode } from './auth-code';

describe('AuthCode', () => {
  let component: AuthCode;
  let fixture: ComponentFixture<AuthCode>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthCode]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AuthCode);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
