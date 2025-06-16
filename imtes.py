msg = f'TXDA 0011,HELLO,12345\r\n'
im920.write(msg.encode())
print(f"送信: {msg.strip()}")
