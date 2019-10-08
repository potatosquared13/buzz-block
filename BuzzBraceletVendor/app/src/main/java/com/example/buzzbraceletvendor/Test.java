package com.example.buzzbraceletvendor;

public class Test {
    public static void main(String[] args) throws Exception{
        // Client jia = new Client(new File("aoyama-jia.key"));
        // Node node = new Node(new File("aoyama-co-coffee.key"));
        // node.start();
        // System.out.println(node.control.client.getIdentity());
        // Thread.sleep(4000);
        // node.sendTransaction(jia.getIdentity(), 1.0);
        // Thread.sleep(60000);
        // node.stop();
        long start = System.nanoTime();
        Thread.sleep(10000);
        System.out.println(System.nanoTime() - start);
    }
}