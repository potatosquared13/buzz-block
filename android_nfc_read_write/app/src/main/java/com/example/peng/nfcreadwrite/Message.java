package com.example.peng.nfcreadwrite;

public class Message{
    public int type;
    public String data;
    public Message(int t, String d){
        type = t;
        data = d;
    }
}